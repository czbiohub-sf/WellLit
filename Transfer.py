from enum import Enum
from datetime import datetime
import uuid, logging
import numpy as np

# TODO: figure out a better way of assigning a plate-name
# TODO: possible: create TransferSequence class
DEST = 'destination-plate'


class TError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class TStatus(Enum):
    uncompleted = 0
    completed = 1
    skipped = 2
    failed = 3

    def color(self):
        return {'uncompleted': 'gray', 'failed': 'red', 'completed': 'blue', 'skipped': 'yellow'}[self.name]


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
        self['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def resetTransfer(self):
        self['status'] = TStatus.uncompleted
        self['timestamp'] = None


'''
TransferProtocol contains a sequence of transfers 
* Transfers are stored in a dict that indexes by unique id's
* Exposes functions which update status of transfers, synchronizes lists and flags with updates
* Provides database like functionality for higher level transfer managements


Transfers should only exist in one single place, inside a TransferProtocol dict[id] = tf. Internally transfers are
referenced by unique_id and moved between lists like completed, skipped, etc. 

'''


class TransferProtocol(object):

    def __init__(self, id_type='uid'):
        self.id_type = id_type
        self.transfers = {}
        self.current_uid = None
        self.lists = {'uncompleted': [], 'completed': [], 'skipped': [], 'failed': [], 'target': None}
        self.error_msg = ''
        self.msg = ''
        self.override = False
        self.canUndo = False
        self._current_idx = 0
        self.tf_seq = np.array(0, dtype=object)

    '''
    buildTransferProtocol and step should be implemented in inherited classes according to the use-case application
    '''
    def buildTransferProtocol(self):
        '''
        Populates a transfer sequence of Transfer objects in a specified order, and assigned unique ids to each Transfer
        '''
        pass

    def step(self):
        '''
        default behavior to perform when iterating through each transer in the transfer sequence
        '''
        pass

    def sortTransfers(self):
        self.lists = {'uncompleted': [], 'completed': [], 'skipped': [], 'failed': [],
                      'target': self.transfers[self.current_uid].id}
        for transfer in self.transfers.values():
            self.lists[self.transfers[transfer.id]['status']].append(transfer.id)

    def tf_id(self):
        curr_tf = self.transfers[self.current_uid]
        if self.id_type == 'uid':
            return curr_tf.id[0:8]
        else:
            return str(curr_tf['source_well'] + '->' + curr_tf['dest_well'])

    def canUpdate(self):
        current_transfer = self.transfers[self.current_uid]
        if current_transfer['timestamp'] is None:
            return True
        else:
            self.log('Cannot update transfer: %s, status is already marked as %s \n' %
                     (self.tf_id(), self.transfers[self.current_uid]['status']))
            raise TError(self.msg)

    def complete(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.completed)
            self.log('transfer complete: %s' % self.tf_id())
            self.step()

    def skip(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.skipped)
            self.log('transfer skipped: %s' % self.tf_id())
            self.step()

    def failed(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.failed)
            self.log('transfer failed: %s' % self.tf_id())
            self.step()

    def undo(self):
        if self.canUndo:
            if not self.plateComplete():
                self.current_idx_decrement()

            self.transfers[self.current_uid].resetTransfer()
            self.canUndo = False
            self.log('transfer marked incomplete: %s' % self.tf_id())
        else:
            self.log('Cannot undo previous operation')

    def log(self, msg: str):
        self.msg = msg
        logging.info(msg)

    def protocolComplete(self):
        for tf in self.tf_seq:
            if self.transfers[tf].status == TStatus.uncompleted:
                return False
        self.msg = 'Transfer Protocol Complete'
        self.log(self.msg)
        return True

    def current_idx_increment(self, steps=1):
        self._current_idx += steps
        self.synchronize()

    def current_idx_decrement(self):
        self._current_idx -= 1
        self.synchronize()

    def synchronize(self):
        self.current_uid = self.tf_seq[self._current_idx]






