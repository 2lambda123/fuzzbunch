
import os.path
import ops
from util.DSZPyLogger import getLogger, WARNING
from ops.psp.actions import PSPManager, RegQueryAction, DirListAction, DoNotAction, ScriptAction, SafetyCheckAction
from ops.ActionFramework import XMLConditionalActionDataSource, ActionManager, XMLAttributeActionDataSource
import dsz.ui
import defusedxml.ElementTree

psplog = getLogger('genericPSP')
psplog.setFileLogLevel(WARNING)
xmltoattributemap = {'regkey': RegQueryAction, 'directory': DirListAction}
xmltoactionmap = {'donot': DoNotAction, 'script': ScriptAction, 'safetycheck': SafetyCheckAction}

def findConfig(vendor):
    """This function returns the path to the configuration file for a given vendor.
    Parameters:
        - vendor (str): The name of the vendor whose configuration file is being searched for.
    Returns:
        - str: The path to the configuration file for the given vendor.
    Processing Logic:
        - Joins the vendor name with the file name and the path to the data directory.
        - Uses the .format() method to insert the vendor name into the file name.
        - Returns the full path to the configuration file."""
    
    return os.path.join(ops.DATA, 'pspFPs', '{0}-fp.xml'.format(vendor))

def findActions(vendor):
    """Function to find the actions.xml file for a given vendor.
    Parameters:
        - vendor (str): Name of the vendor.
    Returns:
        - str: Path to the actions.xml file for the given vendor.
    Processing Logic:
        - Joins the vendor name with the 'pspFPs' and 'actions.xml' strings.
        - Uses the os.path.join() function to create a valid file path.
        - Returns the file path as a string."""
    
    return os.path.join(ops.DATA, 'pspFPs', '{0}-actions.xml'.format(vendor))

def main(vendor):
    """"Executes actions for a given vendor and returns a list of PSPs associated with that vendor.
    Parameters:
        - vendor (str): The name of the vendor to search for.
    Returns:
        - psps (list): A list of PSP objects associated with the given vendor.
    Processing Logic:
        - Searches for the config file for the given vendor.
        - If the config file does not exist, returns None.
        - Parses the config file and retrieves the root actions.
        - Uses the PSPManager class to add the vendor and execute the actions.
        - If the PSPManager is valid, retrieves all PSPs associated with the vendor.
        - If the PSPManager is not valid, logs an error and returns None.
        - Searches for the action file for the given vendor.
        - If the action file exists, parses it and retrieves the root actions.
        - Uses the ActionManager class to validate and execute the actions.
        - If the ActionManager fails to validate, logs an error and returns None.
        - If no PSPs are found, logs a message and returns None.""""
    
    psps = []
    fpfile = findConfig(vendor)
    if (not os.path.exists(fpfile)):
        return None
    with open(fpfile, 'r') as fd:
        xmldata = defusedxml.ElementTree.parse(fd).getroot()
    atpkgs = XMLAttributeActionDataSource(xmldata, xmltoattributemap).GetRootActions()
    pspmgr = PSPManager()
    for atpkg in atpkgs:
        pspmgr.addVendor(atpkg)
    if pspmgr.valid:
        pspmgr.Execute()
        psps = pspmgr.GetAllPSPs()
        for psp in psps:
            if (psp.vendor is None):
                psp.vendor = vendor
    else:
        psplog.critical("This vendor's config file is not valid: {0}".format(vendor))
        return None
    psplog.debug('I found {0} PSPs for Vendor {1}'.format(len(psps), vendor))
    psplog.debug('PSP objects: {0}'.format(psps))
    actfile = findActions(vendor)
    if os.path.exists(actfile):
        with open(actfile, 'r') as fd:
            xmldata = defusedxml.ElementTree.parse(fd).getroot()
        actmgr = ActionManager(XMLConditionalActionDataSource(xmldata, xmltoactionmap, psps).GetRootActions())
        fails = actmgr.Validate()
        if (len(fails) == 0):
            psplog.info('Executing actions for: {0}'.format(vendor))
            psplog.debug('actmgr: {0}'.format(actmgr))
            actmgr.Execute()
        else:
            psplog.critical("This vendor's action file is not valid: {0}\n{1}".format(vendor, fails))
            return None
    if (len(psps) == 0):
        dsz.ui.Echo('I found 0 Products for {0}'.format(vendor), dsz.GOOD)
        return None
    return psps
