from enum import Enum
from datetime import datetime
import uuid, logging
import numpy as np
from abc import ABC, abstractmethod


class TError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class TConfirm(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class TStatus(Enum):
    uncompleted = 0
    completed = 1
    skipped = 2
    failed = 3
    started = 4

    def color(self):
        return {'uncompleted': 'gray', 'failed': 'red', 'completed': 'blue', 'skipped': 'yellow', 'started': 'green'}[self.name]


class Transfer(dict):
    """
    Represents a unique transfer from well/tube to well/tube.
    """

    def __init__(self, unique_id,
                 source_plate=None, dest_plate=None, source_well=None, dest_well=None,
                 source_tube=None, dest_tube=None,
                 timestamp=None, status: TStatus = TStatus.uncompleted):
        self['source_plate'] = source_plate
        self['source_well'] = source_well
        self['dest_plate'] = dest_plate
        self['dest_well'] = dest_well
        self['status'] = status.name
        self['timestamp'] = timestamp
        self['source_tube'] = source_tube
        self['dest_tube'] = dest_tube
        self.status = status
        self.id = unique_id

    def updateStatus(self, status: TStatus):
        self.status = status
        self['status'] = status.name
        # only mark timestamp if the status is marked with a finishing status: skipped, failed, completed.
        if status is not TStatus.started and status is not TStatus.uncompleted:
            self['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def resetTransfer(self):
        self['status'] = TStatus.uncompleted.name
        self['timestamp'] = None
        self['source_tube'] = None


'''
TransferProtocol contains a sequence of transfers 
* Transfers are stored in a dict that indexes by unique id's
* Exposes functions which update status of transfers, synchronizes lists and flags with updates
* Provides database like functionality for higher level transfer managements


Transfers should only exist in one single place, inside a TransferProtocol dict[id] = tf. Internally transfers are
referenced by unique_id and moved between lists like completed, skipped, etc. 

'''


class TransferProtocol(ABC):

    def __init__(self, id_type='uid'):
        self.id_type = id_type
        self.transfers = {}
        self.current_uid = None
        self.current_transfer = None
        self.lists = {'uncompleted': [], 'completed': [], 'skipped': [], 'failed': [], 'started': [], 'target': None}
        self.error_msg = ''
        self.msg = ''
        self.override = False
        self.canUndo = False
        self.unDid = False
        self._current_idx = 0
        self.tf_seq = np.array(0, dtype=object)

    @abstractmethod
    def buildTransferProtocol(self):
        '''
        Populates a transfer sequence of Transfer objects in a specified order, and assigned unique ids to each Transfer
        '''
        pass

    @abstractmethod
    def step(self):
        '''
        default behavior to perform when iterating through each transer in the transfer sequence
        must set self.canUndo flag
        '''
        pass

    def sortTransfers(self):
        self.lists = {'uncompleted': [], 'completed': [], 'skipped': [], 'failed': [], 'started': [],
                      'target': None}
        if self.transfers[self.current_uid].status is TStatus.started:
            self.lists['target'] = self.transfers[self.current_uid]
        else:
            self.lists['target'] = None
        for tf_id in self.transfers.keys():
            self.lists[self.transfers[tf_id]['status']].append(tf_id)

    def tf_id(self):
        self.synchronize()
        curr_tf = self.transfers[self.current_uid]
        if self.id_type == 'uid':
            return curr_tf.id[0:8]
        else:
            if curr_tf['source_well'] is not None:
                return str(curr_tf['source_well'] + '->' + curr_tf['dest_well'])
            if curr_tf['source_tube'] is not None:
                return str(curr_tf['source_tube'] + '->' + curr_tf['dest_well'])

    def canUpdate(self):
        self.synchronize()
        self.sortTransfers()
        current_transfer = self.transfers[self.current_uid]
        if current_transfer['timestamp'] is None:
            return True
        else:
            self.log('Cannot update transfer: %s, status is already marked as %s ' %
                     (self.tf_id(), self.transfers[self.current_uid]['status']))
            raise TError(self.msg)

    def complete(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.completed)
            self.log('transfer complete: %s' % self.tf_id())
            self.step()

    def start(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.started)
            self.log('transfer started: %s' % self.tf_id())
            self.step()

    def skip(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.skipped)
            # self.log('transfer skipped: %s' % self.tf_id())
            self.step()
            self.synchronize()
            self.transfers[self.current_uid].updateStatus(TStatus.started)

    def failed(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.failed)
            # self.log('transfer failed: %s' % self.tf_id())
            self.step()
            self.synchronize()
            self.transfers[self.current_uid].updateStatus(TStatus.started)

    def undo(self):
        """
        When a transfer is undone:
        - there must be at least one 'finished state' transfer: skipped, failed, completed.
        - The current started transfer is reset. index decrements one, resets the previous transfer, then re-starts it.
        - From there that previous transfer can be marked as skipped, failed, or completed.
        """
        self.synchronize()
        self.sortTransfers()
        if self.canUndo:

            # mark the current started transfer as uncomplete, decrement, mark uncomplete, then re-start.
            self.transfers[self.current_uid].resetTransfer()
            self.current_idx_decrement()
            self.transfers[self.current_uid].resetTransfer()
            self.transfers[self.current_uid].updateStatus(TStatus.started)
            self.sortTransfers()
            self.canUndo = False
            self.log('transfer marked incomplete: %s' % self.tf_id())
        else:
            self.log('Cannot undo previous operation')
            raise TError('Cannot undo previous operation')

    def log(self, msg: str):
        self.msg = msg
        logging.info(msg)

    def protocolComplete(self):
        self.sortTransfers()
        for tf in self.tf_seq:
            if self.transfers[tf].status == TStatus.uncompleted:
                return False
        self.msg = 'Transfer Protocol Complete'
        self.log(self.msg)
        return True

    def current_idx_increment(self, steps=1):
        self._current_idx += steps
        self._current_idx = min(self._current_idx, len(self.tf_seq)-1)
        self.synchronize()

    def current_idx_decrement(self):
        self._current_idx -= 1
        self._current_idx = max(self._current_idx, 0)
        self.synchronize()

    def synchronize(self):
        self.current_uid = self.tf_seq[self._current_idx]
        self.current_transfer = self.transfers[self.current_uid]







