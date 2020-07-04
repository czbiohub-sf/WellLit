from enum import Enum
from datetime import datetime
import uuid, logging
import numpy as np

# TODO: figure out a better way of assigning a plate-name
# TODO: possible: create TransferSequence class
DEST = 'destination-plate'

class TStatus(Enum):
    uncompleted = 0
    completed = 1
    skipped = 2
    failed = 3

    def color(self):
        return {'uncompleted': 'gray', 'failed': 'red', 'completed': 'blue', 'skipped': 'yellow'}[self.name]


class Transfer(dict):
    """
    Dict like object that contains transfer information.
    """

    def __init__(self, source_plate: str, dest_plate: str, source_well: str, dest_well: str, unique_id: str,
                 timestamp=None, status: TStatus = TStatus.uncompleted):
        self['source_plate'] = source_plate
        self['source_well'] = source_well
        self['dest_plate'] = dest_plate
        self['dest_well'] = dest_well
        self['status'] = status.name
        self['timestamp'] = timestamp
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
TransferProtocol builds a sequence of transfers from a dataframe
* Transfers are stored in a dict that indexes by unique id's for all internal transfer management
* Exposes functions which update status of transfers, synchronizes lists and flags with updates


Transfers should only exist in one single place, inside a TransferProtocol dict[id] = tf. Internally transfers are
referenced by unique_id and moved between lists like completed, skipped, etc. 

'''


class TransferProtocol(object):

    def __init__(self, df=None, id_type = 'uid'):
        self.df = df
        self.id_type = id_type
        self.transfers = {}
        self.transfers_by_plate = {}
        self.lists = {'uncompleted': [], 'completed': [], 'skipped': [], 'failed': [], 'target': None}
        self.error_msg = ''
        self.msg = ''
        self.override = False
        self.canUndo = False

        if df is not None:
            self.plate_names = self.df['PlateName'].unique()

            # organize transfers into a dict by unique_id, collect id's into lists by plateName
            for plate_name in self.plate_names:
                plate_df = self.df[self.df['PlateName'] == plate_name]
                plate_transfers = []
                for idx, plate_df_entry in plate_df.iterrows():
                    src_plt = plate_df_entry[0]
                    dest_plt = DEST
                    src_well = plate_df_entry[1]
                    dest_well = plate_df_entry[2]
                    unique_id = str(uuid.uuid1())

                    tf = Transfer(src_plt, dest_plt, src_well, dest_well, unique_id)
                    plate_transfers.append(unique_id)
                    self.transfers[unique_id] = tf

                self.transfers_by_plate[plate_name] = plate_transfers

            # produce numpy array of ids to be performed in a sequence, grouped by plate.
            current_idx = 0
            self.num_transfers = len(self.transfers)
            self.tf_seq = np.empty(self.num_transfers, dtype=object)

            for plate in self.plate_names:
                plate = self.transfers_by_plate[plate]
                for tf_id in plate:
                    self.tf_seq[current_idx] = tf_id
                    current_idx += 1

            self._current_idx = 0  # index in tf_seq
            self._current_plate = 0  # index in plate_names

            self.current_uid = self.tf_seq[self._current_idx]
            self.current_plate_name = self.plate_names[self._current_plate]
            self.num_plates = len(self.plate_names)
            self.plate_sizes = {}
            for plate in self.plate_names:
                self.plate_sizes[plate] = len(self.transfers_by_plate[plate])
            self.sortTransfers()

    def canUpdate(self):
        current_transfer = self.transfers[self.current_uid]

        if current_transfer['timestamp'] is None:
            return True
        else:
            self.log('Cannot update transfer: %s, status is already marked as %s' %
                     (current_transfer.id[0:8], current_transfer['status']))
            if self.plateComplete():
                self.log('Plate %s is complete, press next plate to continue' % self.current_plate_name)
            return False

    def step(self):
        """
        Moves index to the next transfer in a plate. If plate full or transfer complete, raises flag
        """
        self.sortTransfers()
        self.canUndo = True

        if self.plateComplete():
            if self.protocolComplete():
                self.log('TransferProtocol is complete')
            else:
                self.log('Plate %s completed' % self.current_plate_name)
        else:
            self.current_idx_increment()

    def nextPlate(self):
        self.canUndo = False
        if self.plateComplete():
            if not self.protocolComplete():
                self.current_plate_increment()
                self.current_idx_increment()
                self.log('Plate %s loaded' % self.current_plate_name)
            else:
                self.log('TransferProtocol is complete')

        else:
            self.log('Warning: Plate %s not yet complete' % self.current_plate_name)
            skipped_transfers_in_plate = list(
                set(self.lists['uncompleted']) &
                set(self.transfers_by_plate[self.current_plate_name]))

            self.msg = 'Skipping this plate will skip %s remaining transfers. Are you sure?' % len(skipped_transfers_in_plate)

            if self.override:
                self.override = False
                # collect leftover transfers
                skipped_transfers_in_plate = list(
                     set(self.lists['uncompleted']) &
                     set(self.transfers_by_plate[self.current_plate_name]))

                # Mark uncomplete transfers as skipped for this plate
                for tf in skipped_transfers_in_plate:
                    self.transfers[tf].updateStatus(TStatus.skipped)

                self.log('Remaining %s transfers in plate %s skipped' %
                         (len(skipped_transfers_in_plate), self.current_plate_name))

                if self.protocolComplete():
                    pass
                else:
                    self.current_plate_increment()
                    self.current_idx_increment(steps=len(skipped_transfers_in_plate))
                    self.log('Plate %s loaded' % self.current_plate_name)

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
        print(msg)
        logging.info(msg)

    def plateComplete(self):
        for tf in self.transfers_by_plate[self.current_plate_name]:
            if self.transfers[tf].status == TStatus.uncompleted:
                return False
        return True

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
        self._current_plate -= 1
        self.synchronize()

    def current_plate_increment(self):
        self._current_plate += 1
        self.synchronize()

    def current_plate_decrement(self):
        self._current_plate -= 1
        self.synchronize()

    def synchronize(self):
        self.current_uid = self.tf_seq[self._current_idx]
        self.current_plate_name = self.plate_names[self._current_plate]






