from enum import Enum
from datetime import datetime


class TStatus(Enum):
    uncompleted = 0
    completed = 1
    skipped = 2
    failed = 3


class Transfer(dict):
    def __init__(self, source_plate: str, dest_plate: str, source_well: str, dest_well: str, unique_id,
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

    def resetTransfer(self):
        self.updated = False
        self['status'] = TStatus.uncompleted
        self['timestamp'] = None


class PlateTransfer(dict):
    def __init__(self, source_plate):
        self['source_plate'] = source_plate
        self['dest_plate'] = dest_plate