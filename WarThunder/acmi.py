'''
Module to make Tacview compatible ACMI files - see https://www.tacview.net/documentation/acmi/en/
'''


import os
from random import randint
import datetime as dt


MAX_NUM_OBJS     = 0xFFFFFFFFFFFFFFFE
header_mandatory = ('FileType={filetype}\n' 
                    'FileVersion={acmiver}\n'
                    '0,ReferenceTime={reftime}Z\n')


class ACMI(object):
    '''
    Class used to create and maintain a given ACMI file used by the
    downloadable program Tacview
    '''
        
    def __init__(self, num_objs: int = 1):
        '''
        Initialize class object and create a member dict named "obj_ids" to
        hold unique/valid HEX ID values for each object to be displayed
        
        Args:
            num_objs:
                Number of objects to simulaneously display in Tacview
        '''
        
        self.obj_ids = {}
        
        if num_objs > MAX_NUM_OBJS:
            raise Exception('Too many objects specified - cannot be more than {}'.format(MAX_NUM_OBJS))
        
        for obj_num in range(num_objs):
            self.add_object()
        
    def add_object(self) -> int:
        '''
        Append a new and unique hex object ID to the self.obj_ids dict
        
        Returns:
                Hex ID for new object
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
        
    def create(self, file_name: str, file_type: str = 'text/acmi/tacview', acmi_ver: str = '2.1'):
        '''
        Create an ACMI file with a basic header
        
        Args:
            file_name:
                Full filepath or filename of ACMI file to create
            file_type:
                See default
            acmi_ver:
                See default
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
    
    def get_timestamp(self) -> dt.datetime:
        '''
        Find the true time to provide accurate sample timestamps
        
        Returns:
                Current UTC time
        '''
        
        return dt.datetime.utcnow()

    def insert_user_header(self, header_content: dict) -> bool:
        '''
        Insert special header parameters
        (NOTE - DO THIS BEFORE INSERTING ANY ENTRIES)**************************
        
        Args:
            header_content:
                Header property names and values
        
        Returns:
            Success:
                Whether or not the operation was successful
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
    
    def format_user_header(self, header_content: dict) -> str:
        '''
        Create an ACMI file header with user defined fields/values (does not
        include mandatory header fields)
        
        Args:
            header_content:
                Header property names and values
        
        Returns:
                Formatted header string
        '''
        
        if not type(header_content) == dict:
            raise TypeError('"header_content" must be of type dict, not {}'.format(type(header_content)))
        
        header_list = ['0,{}={}'.format(key, header_content[key]) for key in header_content.keys()]
        return '\n'.join(header_list) + '\n'
    
    def insert_entry(self, obj_num: int, data: dict, timestamp: bool = True) -> bool:
        '''
        Log a single entry of telemetry in the ACMI file for a given object
        
        Args:
            obj_num:
                Object number as represented in the ID-lookup dictionary
                self.obj_ids
            data:
                Object information to be included in the new entry
        
        Returns:
            Success:
                Whether or not the operation was successful
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
    
    def format_entry(self, obj_num: int, data: dict, timestamp: bool = True):
        '''
        Create a single entry of telemetry for a given object
        
        Args:
            obj_num:
                Object number as represented in the ID-lookup dictionary
                self.obj_ids
            data:
                Object information to be included in the new entry
        
        Returns:
                Formatted entry string
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
    
    
    
    
