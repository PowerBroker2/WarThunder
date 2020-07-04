import os
from random import randint
import datetime as dt


MAX_NUM_OBJS     = 0xFFFFFFFFFFFFFFFE
header_mandatory = ('FileType={filetype}\n' 
                    'FileVersion={acmiver}\n'
                    '0,ReferenceTime={reftime}Z\n')


class ACMI(object):
    '''
    Description:
    ------------
    Class used to create and maintain a given ACMI file used by the
    downloadable program Tacview
    '''
        
    def __init__(self, num_objs=1):
        '''
        Description:
        ------------
        Initialize class object and create a member dict named "obj_ids" to
        hold unique/valid HEX ID values for each object to be displayed
        
        :param num_objs: int - number of objects to simulaneously display in Tacview
        
        :return self.obj_ids: dict - lookup table of unique object HEX IDs
        '''
        
        self.obj_ids = {}
        
        if num_objs > MAX_NUM_OBJS:
            raise Exception('Too many objects specified - cannot be more than {}'.format(MAX_NUM_OBJS))
        
        for obj_num in range(num_objs):
            self.add_object()
        
    def add_object(self):
        '''
        Description:
        ------------
        Append a new and unique hex object ID to the self.obj_ids dict
        
        :return id_: str - hex ID for new object
        '''
        
        id_ = str(hex(randint(1, MAX_NUM_OBJS + 2))[2:]).upper()
        
        # Ensure each ID is unique
        while id_ in self.obj_ids.values():
            id_ = str(hex(randint(1, MAX_NUM_OBJS + 2))[2:]).upper()
        
        try:
            obj_num = str(int(max(self.obj_ids.keys())) + 1)
        except ValueError:
            obj_num = '0'
        
        self.obj_ids[str(obj_num)] = id_
        
        return id_
        
    def create(self, file_name, file_type='text/acmi/tacview', acmi_ver='2.1'):
        '''
        Description:
        ------------
        Create an ACMI file with a basic header
        
        :param file_name: str - full filepath or filename of ACMI file to create
        
        :return: void
        '''
        
        self.file_name      = file_name
        self.reference_time = self.get_timestamp()
        
        if not self.file_name.endswith('.acmi'):
            self.file_name += '.acmi'
        
        dir_name = os.path.dirname(file_name)
        
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        
        with open(self.file_name, 'w') as log:
            log.write(header_mandatory.format(filetype=file_type,
                                              acmiver=acmi_ver,
                                              reftime=self.get_timestamp().isoformat()))
    
    def get_timestamp(self):
        '''
        Description:
        ------------
        Find the true time to provide accurate sample timestamps
        
        :return: datetime - current UTC time
        '''
        
        return dt.datetime.utcnow()

    def insert_user_header(self, header_content: dict):
        '''
        Description:
        ------------
        Insert special header parameters
        (NOTE - DO THIS BEFORE INSERTING ANY ENTRIES)**************************
        
        :param header_content: dict - header property names and values
        
        :return: bool - whether or not the operation was successful
        '''
        
        if not type(header_content) == dict:
            raise TypeError('"header_content" must be of type dict, not {}'.format(type(header_content)))
        
        header = self.format_user_header(header_content)
        
        try:
            with open(self.file_name, 'a') as log:
                log.write(header)
            return True
        
        except FileNotFoundError:
            print('ERROR - ACMI file not found')
            return False
    
    def format_user_header(self, header_content: dict):
        '''
        Description:
        ------------
        Create an ACMI file header with user defined fields/values (does not
        include mandatory header fields)
        
        :param header_content: dict - header property names and values
        
        :return: str - formatted header string
        '''
        
        if not type(header_content) == dict:
            raise TypeError('"header_content" must be of type dict, not {}'.format(type(header_content)))
        
        header_list = ['0,{}={}'.format(key, header_content[key]) for key in header_content.keys()]
        return '\n'.join(header_list) + '\n'
    
    def insert_entry(self, obj_num, data: dict, timestamp=True):
        '''
        Description:
        ------------
        Log a single entry of telemetry in the ACMI file for a given object
        
        :param obj_num: int  - object number as represented in the ID-lookup
                               dictionary self.obj_ids
        :param data:    dict - object information to be included in the new entry
        
        :return: bool - whether or not the operation was successful
        '''
        
        if not type(data) == dict:
            raise TypeError('"data" must be of type dict, not {}'.format(type(data)))
        
        entry = self.format_entry(obj_num, data, timestamp)
        
        try:
            with open(self.file_name, 'a') as log:
                log.write(entry)
            return True
        
        except FileNotFoundError:
            print('ERROR - ACMI file not found')
            return False
    
    def format_entry(self, obj_num, data: dict, timestamp=True):
        '''
        Description:
        ------------
        Create a single entry of telemetry for a given object
        
        :param obj_num: int  - object number as represented in the ID-lookup
                               dictionary self.obj_ids
        :param data:    dict - object information to be included in the new entry
        
        :return: str - formatted entry string
        '''
        
        if not type(data) == dict:
            raise TypeError('"data" must be of type dict, not {}'.format(type(data)))
        
        if timestamp:
            current_time = self.get_timestamp()
            diff_sec     = (current_time - self.reference_time).total_seconds()
            entry = '#{:0.2f}\n{},'.format(diff_sec, self.obj_ids[str(obj_num)])
        else:
            entry = '{},'.format(self.obj_ids[str(obj_num)])
        
        entry += ','.join('{}={}'.format(name, data[name]).replace(',', '\,') for name in data.keys())
        entry += '\n'
        
        return entry
    
    
    
    
