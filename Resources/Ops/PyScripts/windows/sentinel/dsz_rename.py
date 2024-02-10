
import sys
import glob
import os
import shutil
import defusedxml.ElementTree

DSZ_NS = '{urn:mca:db00db84-8b5b-2141-a632b5980175d3c6}'
DATALOG_TAG = ('%sDataLog' % DSZ_NS)
COMMANDDATA_TAG = ('%sCommandData' % DSZ_NS)
TASKRESULT_TAG = ('%sTaskResult' % DSZ_NS)
FILESTART_TAG = ('%sFileStart' % DSZ_NS)
FILELOCALNAME_TAG = ('%sFileLocalName' % DSZ_NS)
LOCAL_NAME_KEY = 'local_name'
REMOTE_NAME_KEY = 'remote_name'
SAFE_EXTS = ['.gif', '.bmp', '.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.vsd', '.txt', '.cfg', '.csv', '.pdf', '.rtf', '.log', '.xml', '.rar', '.gz', '.zip', '.bz2', '.tgz']

def main(file_to_read, output_dir):
    """Function:
        Main function that renames and copies files from a specified directory to a specified output directory.
    Parameters:
        - file_to_read (str): The path to the file that contains the list of files to be renamed and copied.
        - output_dir (str): The path to the directory where the renamed and copied files will be saved.
    Returns:
        - None: This function does not return any value.
    Processing Logic:
        - Checks if the file to be read is a completed result file.
        - Gets the task ID from the file name.
        - Uses the task ID to search for all files that match the pattern '*-get_*_%s_*.xml' in the same directory as the file to be read.
        - Stores all the files in a dictionary, with the task ID as the key and the file ID, remote name, and local name as the values.
        - Creates a destination directory for the renamed and copied files.
        - Copies the files from the source directory to the destination directory, renaming them if necessary."""
    
    if (not is_completed_result(file_to_read)):
        return
    task_id = file_to_read.split('_')[2]
    path_to_glob = os.path.join(os.path.dirname(file_to_read), ('*-get_*_%s_*.xml' % task_id))
    all_gets = glob.glob(path_to_glob)
    if (len(all_gets) <= 0):
        return
    all_files = {}
    for get_file in all_gets:
        base_name = os.path.basename(get_file)
        task_id = base_name.split('-')[0]
        tree = defusedxml.ElementTree.parse(get_file)
        data_log = tree.getiterator(DATALOG_TAG)[0]
        command_data = data_log.find(COMMANDDATA_TAG)
        file_start = command_data.find(FILESTART_TAG)
        file_local_name = command_data.getiterator(FILELOCALNAME_TAG)
        if (file_start is not None):
            file_id = file_start.get('fileId')
            remote_name = file_start.get('remoteName')
            all_files = safe_store_by_ids(all_files, task_id, file_id, REMOTE_NAME_KEY, remote_name)
        elif len(file_local_name):
            file_local_name = file_local_name[0]
            file_id = file_local_name.get('fileId')
            local_name = file_local_name.text
            all_files = safe_store_by_ids(all_files, task_id, file_id, LOCAL_NAME_KEY, local_name)
        else:
            pass
    target_dir = os.path.dirname(os.path.dirname(file_to_read))
    dest_dir = os.path.join(output_dir, 'GetFiles_Renamed')
    if (not os.path.exists(dest_dir)):
        os.makedirs(dest_dir)
    copy_files_from_dict(all_files, target_dir, dest_dir)

def is_completed_result(file_to_parse):
    """Checks if the task result in the provided XML file is completed.
    Parameters:
        - file_to_parse (str): The path to the XML file to be parsed.
    Returns:
        - bool: True if the task result is completed, False otherwise.
    Processing Logic:
        - Parse the XML file using defusedxml library.
        - Get the data log element from the parsed tree.
        - Find the command data element within the data log.
        - Find the task result element within the command data.
        - Check if the task result is not None and its text is '0x00000000'.
        - If so, return True, otherwise return False.
        - If any error occurs during the process, return False."""
    
    try:
        tree = defusedxml.ElementTree.parse(file_to_parse)
        data_log = tree.getiterator(DATALOG_TAG)[0]
        command_data = data_log.find(COMMANDDATA_TAG)
        task_result = command_data.find(TASKRESULT_TAG)
        if ((task_result is not None) and (task_result.text == '0x00000000')):
            return True
        else:
            return False
    except:
        return False

def safe_store_by_ids(dictionary, task_id, file_id, key, value):
    """Function to safely store values in a nested dictionary.
    Parameters:
        - dictionary (dict): The dictionary to store the values in.
        - task_id (int): The task ID to use as the first level key.
        - file_id (int): The file ID to use as the second level key.
        - key (str): The key to use for the value.
        - value (any): The value to be stored.
    Returns:
        - dictionary (dict): The updated dictionary with the new value stored.
    Processing Logic:
        - If the task ID is not already a key in the dictionary, create a new key-value pair with the task ID as the key and a nested dictionary as the value.
        - If the file ID is not already a key in the nested dictionary, create a new key-value pair with the file ID as the key and a nested dictionary as the value.
        - Add the key-value pair to the nested dictionary using the given key and value.
        - Return the updated dictionary."""
    
    if (not dictionary.has_key(task_id)):
        dictionary[task_id] = {file_id: {key: value}}
        return dictionary
    if (not dictionary[task_id].has_key(file_id)):
        dictionary[task_id][file_id] = {key: value}
        return dictionary
    dictionary[task_id][file_id][key] = value
    return dictionary

def copy_files_from_dict(all_files, target_dir, dest_dir):
    """Copies files from a dictionary to a specified destination directory.
    Parameters:
        - all_files (dict): A dictionary containing task IDs as keys and a dictionary of file IDs and names as values.
        - target_dir (str): The path to the directory where the files are currently located.
        - dest_dir (str): The path to the directory where the files will be copied to.
    Returns:
        - None: This function does not return any value.
    Processing Logic:
        - Loops through each task ID in the dictionary.
        - Loops through each file ID and name in the task's dictionary.
        - Constructs the path to the file to be copied.
        - Creates a new destination name for the file.
        - Checks if the file extension is safe and adds a '.r' extension if not.
        - Constructs the path to the destination file.
        - Skips the file if it already exists in the destination directory.
        - Attempts to copy the file to the destination directory.
        - Ignores any errors that occur during the copying process."""
    
    for (task_id, files) in all_files.items():
        for (file_id, names) in files.items():
            to_copy = os.path.join(target_dir, 'GetFiles', names[LOCAL_NAME_KEY])
            new_dest_name = os.path.basename(names[REMOTE_NAME_KEY])
            ext = os.path.splitext(new_dest_name)[1]
            if ((ext.lower() not in SAFE_EXTS) and (ext != '')):
                new_dest_name += '.r'
            dest = os.path.join(dest_dir, ('%s_%s_%s' % (task_id, file_id, new_dest_name)))
            if os.path.exists(dest):
                continue
            try:
                shutil.copyfile(to_copy, dest)
            except IOError as e:
                pass
