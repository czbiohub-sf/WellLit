from enum import Enum
from datetime import datetime
import uuid


class TStatus(Enum):
    uncompleted = 0
    completed = 1
    skipped = 2
    failed = 3


class Transfer(dict):
    """
    Dict like object that contains transfer information. Guards against status updates. id for internal use.
    """

    def __init__(self, source_plate: str, dest_plate: str, source_well: str, dest_well: str, unique_id: str,
                 timestamp=None, status: TStatus = TStatus.uncompleted):
        self['source_plate'] = source_plate
        self['source_well'] = source_well
        self['dest_plate'] = dest_plate
        self['dest_well'] = dest_well
        self['status'] = status.name
        self['timestamp'] = timestamp
        self.id = unique_id
        self.updated = False

    def updateStatus(self, status: TStatus):
        if not self.updated:
            self['status'] = status.name
            self['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        else:
            print('Transfer already %s' % self['status'])

    def resetTimestamp(self):
        self['timestamp'] = None

    def resetTransfer(self):
        self.updated = False
        self['status'] = TStatus.uncompleted
        self['timestamp'] = None


'''
TransferProtocol builds a sequence of transfers from a dataframe
* Transfers are stored in a dict that indexes by unique id's for all internal transfer management
* Exposes functions which update status of transfers
* Raises flags when a plate or transfer sequence is complete


Transfers should only exist in one single place, inside a TransferProtocol dict[id] = tf. Internally transfers are
referenced by unique_id and moved between lists like completed, skipped, etc. 

'''


class TransferProtocol():

    def __init__(self, df):
        self.df = df
        self.transfers = {}
        self.transfers_by_plate = {}
        self.lists = {'uncompleted': [], 'completed': [], 'skipped': [], 'failed': []}
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

        self.current_idx = 0  # index in tf_seq
        self.current_plate = 0  # index in plate_names
        self.current_idx_plate = 0  # index within the current plate

        self.current_uid = self.tf_seq[self.current_idx]
        self.current_plate_name = self.plate_names[self.current_plate]
        self.num_plates = len(self.plate_names)
        self.plate_sizes = {}
        for plate in self.plate_names:
            self.plate_sizes[plate] = len(self.transfers_by_plate[plate])

        self.error_msg = ''
        self.override = False
        self.canUndo = False
        self.transferProtocol = False
        self.plateComplete = False

    def canUpdate(self):
        current_transfer = self.transfers[self.tf_seq[self.current_idx]]
        plate_size = self.plate_sizes[self.plate_names[self.current_plate]]

        if self.transfers[self.tf_seq[self.current_idx]]['timestamp'] is None:
            return True
        else:
            self.log('Cannot update transfer: %s, status is already marked as %s' %
                     (current_transfer.id[0:8], current_transfer['status']))
            if self.current_idx_plate == plate_size - 1:
                self.log('Plate %s is complete, press next plate to continue' % self.plate_names[self.current_plate])
            return False

    def log(self, msg: str):
        self.msg = msg
        print(msg)
        logging.info(msg)

    def step(self):
        """
        Moves index to the next transfer in a plate. If plate full or transfer complete, raises flag
        """
        self.sortTransfers()

        if self.current_idx_plate == self.plate_sizes[self.current_plate_name] - 1:
            if self.current_idx == self.num_transfers - 1:
                self.transferProtocolComplete = True
                self.log('TransferProtocol complete')
            else:
                self.plateComplete = True
                self.log('Plate %s completed' % self.current_plate_name)
        else:
            self.current_idx += 1
            self.current_idx_plate += 1
            self.current_uid = self.tf_seq[self.current_idx]

    def nextPlate(self):
        if self.plateComplete:
            self.plateComplete = False
            self.current_plate += 1
            self.current_idx_plate = 0
            self.current_idx += 1
            self.current_plate_name = self.plate_names[self.current_plate]
            self.log('Plate %s loaded' % self.current_plate_name)

        else:
            self.log('Warning: Plate %s not yet complete' % self.current_plate_name)
            if self.override:

                skipped_transfers_in_plate = len(list(set(self.lists['uncompleted']) &
                                                      set(self.transfers_by_plate[self.current_plate_name])))
                self.log('Remaining %s transfers in plate %s skipped' %
                         (skipped_transfers_in_plate, self.plate_names[self.current_plate]))
                self.override = False
                if self.current_plate == self.num_plates - 1:
                    self.log('TransferProtocol complete')
                else:
                    self.plateComplete = False
                    self.current_plate += 1
                    self.current_idx_plate = 0
                    self.current_idx += skipped_transfers_in_plate
                    self.current_plate_name = self.plate_names[self.current_plate]
                    self.log('Plate %s loaded' % self.current_plate_name)

    def sortTransfers(self):
        self.lists = {'uncompleted': [], 'completed': [], 'skipped': [], 'failed': []}
        for transfer in self.transfers.values():
            self.lists[self.transfers[transfer.id]['status']].append(transfer.id)

    def complete(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.completed)
            self.canUndo = True
            self.log('transfer complete: %s' % self.transfers[self.tf_seq[self.current_idx]].id[0:8])
            self.step()

    def skip(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.skipped)
            self.canUndo = True
            self.log('transfer skipped: %s' % self.transfers[self.tf_seq[self.current_idx]].id[0:8])
            self.step()

    def failed(self):
        if self.canUpdate():
            self.transfers[self.current_uid].updateStatus(TStatus.failed)
            self.canUndo = True
            self.log('transfer failed: %s' % self.transfers[self.tf_seq[self.current_idx]].id[0:8])
            self.step()

    def undo(self):
        if self.canUndo:
            self.current_idx_plate -= 1
            self.current_idx -= 1
            self.current_uid = self.tf_seq[self.current_idx]
            self.transfers[self.tf_seq[self.current_idx]].updateStatus(TStatus.uncompleted)
            self.transfers[self.tf_seq[self.current_idx]].resetTimestamp()
            self.canUndo = False
            self.log('transfer marked incomplete: %s' % self.transfers[self.tf_seq[self.current_idx]].id[0:8])
        else:
            self.log('Cannot undo previous operation')

    def _check(self):
        '''
        Check to see if global index and plate index match
        '''
        print(self.tf_seq[self.current_idx] == self.transfers_by_plate[self.current_plate_name][self.current_idx_plate])




