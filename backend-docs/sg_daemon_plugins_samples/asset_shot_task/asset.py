"""
Observe when a new asset is created on ShotGrid, do a name check and perform
file system working directory creation.
"""
from __future__ import print_function  # fix pylint

import os
import getpass
import re
import pprint
from abc import ABCMeta, abstractmethod

import emailutil
from spin_config_manager.config_manager import SpinResolvedConfig
from spin_file_system.products import level_to_product_config
from spin_file_system.directories import (
    Permission, create_staging_root,
    create_shotasset, query_path
)
from spin_file_system.utility import pub_file_ops, get_show_division, get_gid
from spin_file_system.constants import SPIN_ROOT
from spin_usd_util.usd_api import AssetUsd

SELECTED_SHOW = dict(SpinResolvedConfig('usd_show.json',
                                        subdirs='SG_plugin_USD',
                                        merge=True,))['show']

ASSET_STATUS = dict(SpinResolvedConfig('asset_shot_status_list.json',
                                       subdirs='SG_plugin_USD',
                                       merge=True,))['asset_status']

RESOLUTIONS = dict(SpinResolvedConfig('model_publish.json',
                                      subdirs='spin_assettree',
                                      merge=True,))['resolutions']


def match_invalid_char(name):
    """Check if there is invalid character in string.

    Args:
        name (str): string of the name to be checked.

    Returns:
        object: Match object which contain result of check, None if no invalid
            char.
    """
    pattern = re.compile(r"[\W]")  # pylint: disable=anomalous-backslash-in-string
    return pattern.search(name)


def notify_invalid_name(sg, entity, email_list, logger, match):
    """
    Email creator and cc producers that an invalid name is detected and status
     of the entity is set to N/A.

    Args:
        sg (object): Shotgun connection.
        entity (Entity): Asset entity instance.
        email_list (Tuple[list, list]): List of two lists, first is msg_to_list,
            second is msg_cc_list.
        logger (object): Logger handle.
        match (object): Match object which contain result of check, None if no
            invalid char.

    Returns:
        True if successful, False otherwise.
    """
    server = ""
    if sg.info()["analytics_site_name"] == "com_shotgunstudio_spinvfx_staging":
        server = "-staging"
    if not email_list:
        logger.warning("No one to notify")
        return False
    if not emailutil.send_email(
            emailutil.SPIN_EMAIL_HOST, emailutil.SPIN_EMAIL_PORT,
            "noreply@shotgunstudio.com",
            email_list[0],
            "Invalid name for new {}: '{}' in show '{}'"
            "".format(entity.entity["type"],
                      entity.entity["code"],
                      entity.entity["project"]["name"]),
            "Hello {5},\n\n"
            "We tried to auto create work dir for {entity_type}: "
            "'{1}' of show '{2}' "
            "and we detected invalid characters in it. "
            "The name could not contain characters other than"
            " a-z, A-Z, 0-9 and '_'.\n\n"
            "The first invalid character we detected in the name is: '{0}'.\n\n"
            "We'd suggest you set the asset in Shotgrid to N/A status and "
            "remake a new asset without the invalid characters.\n\n"
            "All producers have been notified. "
            "For more information, click this {entity_type} webpage: "
            "https://spinvfx{3}.shotgunstudio.com/detail/{entity_type}/{4}\n\n"
            "- SG Daemon Plugin"
            "".format(match.group(),
                      entity.entity["code"],
                      entity.entity["project"]["name"],
                      server,
                      entity.entity["id"],
                      entity.event["user"]["name"],
                      entity_type=entity.entity["type"]),
            msg_cc_list=email_list[1]):
        logger.warning("Failed to send emails")
        return False
    return True


def notify_invalid_change(sg, entity, email_list, logger, match):
    """
    Email creator that an invalid new name is detected and entity name is rolled
    back.

    Args:
        sg (object): Shotgun connection.
        entity (dict): Asset entity found from shotgun that was checked and
            threshed.
        email_list (list of list): List of two lists, first is msg_to_list, second is
            msg_cc_list.
        logger (object): Logger handle.
        match (object): Match object which contain result of check, None if no
            invalid char.

    Returns:
        True if successful, False otherwise.
    """
    server = ""
    if sg.info()["analytics_site_name"] == "com_shotgunstudio_spinvfx_staging":
        server = "-staging"
    if not email_list:
        logger.warning("No one to notify")
        return False
    if not emailutil.send_email(
            emailutil.SPIN_EMAIL_HOST, emailutil.SPIN_EMAIL_PORT,
            "noreply@shotgunstudio.com",
            email_list[0],
            "Invalid name name change for {}: '{}' in show '{}'"
            "".format(entity["type"],
                      entity["code"],
                      entity["project"]["name"]),
            "Name could not contain characters other than "
            "a-z, A-z, 0-9 and '_'.\n"
            "The first invalid character: '{0}'.\n"
            "Name of {entity_type} rolled back!\n"
            "For more information, check {entity_type} webpage: "
            "https://spinvfx{1}.shotgunstudio.com/detail/{entity_type}/{2}"
            "".format(match.group(),
                      server,
                      entity["id"],
                      entity_type=entity["type"]), ):
        logger.warning("Failed to send emails")
        return False
    return True


def get_lod_list(sg, model_package_list):
    """get lod list from published files of model pacakge"""
    latest_package = sorted(model_package_list,
                            key=lambda i: i["name"][-3:],
                            reverse=True)[0]
    package = sg.find_one(latest_package["type"],
                          [["id", "is", latest_package["id"]]],
                          ["sg_published_files"])
    lod_list = []
    for published_file in package["sg_published_files"]:
        lod = published_file["name"].split(" ")[0].split("_")[-1]
        if lod in RESOLUTIONS:
            lod_list.append(published_file["name"].split(" ")[0].split("_")[-1])
    return lod_list


class Entity:  # pylint: disable=too-many-instance-attributes
    """Shot grid entity, inherited by asset, shot or task.
    Attributes:
        fields (list of str): Fields to find in shotgun, to be defined in
            instances.
        type (str): Entity type. (asset, shot or task)
        sg (object): Shotgun handle.
        logger (object): Spin log handle.
        event (dict): The event caught from event daemon by registerCallbacks.
        entity (dict): Entity found in shotgun.
        event_entity (dict): Entity extracted from event.
    """
    __metaclass__ = ABCMeta

    def __init__(self, sg, logger, event):
        """
        Args:
            sg (object): Shotgun handle.
            logger (object): Spin log handle.
            event (dict): The event caught from event daemon by
                registerCallbacks.
        """
        self.fields = []
        self.type = ""

        self.sg = sg
        self.logger = logger

        self.event = event
        self.entity = None
        self.event_entity = None

    def get_entity_from_id(self, entity_id):
        """Get entity dict from entity id, need to define self.type and
        self.field first.

        Args:
            entity_id (str): Shotgun entity id.

        Returns:
            Dict of entity found in shotgun.
        """
        filters = [["id", "is", entity_id]]
        entity = self.sg.find(self.type, filters, self.fields)

        if not entity:
            self.logger.warning("Could not obtain {} with {} ID {}"
                                .format(self.type, self.type, self))
            return None

        return entity[0]

    def get_entity_from_event(self):
        """Get the linked shot/asset entity and the relevant attributes from the
        event, dict assigned to self.entity.

        Returns:
            True is successful, False otherwise.
        """
        # Obtain entity linked to this event
        if not self.event["entity"]:
            self.logger.warning("No {} linked to this event. Cannot proceed"
                                .format(self.type))
            return False
        self.event_entity = self.event["entity"]
        # Obtain the shot entity linked to this event
        try:
            entity_id = self.event["entity"]["id"]
        except KeyError:
            # The event wasn't formed properly, bail
            self.logger.warning("Got incomplete event that doesn't contain the"
                                " ID of the attached {}".format(self.type))
            return False

        self.entity = self.get_entity_from_id(entity_id)
        pprinter = pprint.PrettyPrinter(indent=4)
        self.logger.info("Got entity:\n\n{}\n\n"
                         .format(pprinter.pformat(self.entity)))
        return True

    def get_email_lists(self):
        """Get creator's email and producers' emails.

        Returns:
            email_list (list of str): Email of the creator of the entity.
            cc_list (list of str): Emails of the producers of the show.
        """
        cc_list = []
        event_user_id = self.event["user"]["id"]
        prodcr_list_list = self.get_producer_list_from_project_id(
            self.entity["project"]["id"])
        producer_list = \
            [prod for prodcr_list in prodcr_list_list for prod in prodcr_list]

        try:
            email_list = [self.get_email_from_userid(event_user_id)]
        except KeyError as error:
            self.logger.error("Could not obtain email of event creator, user ID"
                              ": {}".format(event_user_id))
            print(error)
            return None

        try:
            cc_list = \
                [self.get_email_from_userid(prod["id"])
                 for prod in producer_list]
        except KeyError as error:
            self.logger.info("Could not obtain email of one or more of: "
                             "sg_producer_1, sg_exec_producer, "
                             "sg_supervising_producer_1")
            print(error)
        return email_list, cc_list

    def get_producer_list_from_project_id(self, project_id):  # pylint: disable=invalid-name
        """Return a list of producers from id of the show.

        Args:
            project_id (str): Shotgun id of the show.

        Returns:
            A list of dict, which are HumanUser objects of producers.
        """
        filters = [["id", "is", project_id]]
        fields = ["sg_producer_1", "sg_exec_producer",
                  "sg_supervising_producer_1"]
        show = self.sg.find_one("Project", filters, fields)
        if show:
            list_of_list = [show[field] for field in fields]
            return [prod for prod_list in list_of_list for prod in prod_list]
        self.logger.warning("Could not find Project with id {}.".
                            format(project_id))
        return None

    def get_email_from_userid(self, userid):
        """Get email of a user from user ID.

        Args:
            userid (str): User id.

        Returns:
            Email of the user as string.
        """
        user = self.sg.find_one("HumanUser", [["id", "is", userid]], ["email"])
        return user["email"]

    def invalidate_entity(self):
        """Set entity status to N/A"""
        self.sg.update(self.type, self.entity["id"], {"sg_status_list": "na"})

    def get_entity_code(self):
        """Get entity code from key 'name'.

        Returns:
            Entity code as a string is successful, None otherwise.
        """
        try:
            return self.event_entity["name"]
        except (KeyError, TypeError) as error:
            self.logger.warning("Could not get name from entity")
            print(error)
            return None

    @abstractmethod
    def get_entity_key_values(self):
        """To be implemented"""
        pass


class Asset(Entity):
    """Shotgun asset entity.

    Attributes:
        fields (list of str): Fields to find in shotgun.
        type (str): Entity type. (asset, shot or task)
        folder_create_func (object): Function imported from to do asset root
            directory creation.
    """
    def __init__(self, sg, logger, event):
        """
        Args:
            sg (object): Shotgun handle.
            logger (object): Spin log handle.
            event (dict): The event caught from event daemon by
                registerCallbacks.
        """
        super(Asset, self).__init__(sg, logger, event)
        self.type = "Asset"
        self.sequence_type = 'asset'
        # @${PROJECT_ROOT}/asset/<asset_type>/<asset_name>/${PRODUCTION_TOKEN}/
        # asset/sublayer/${VERSION}/usd/asset.usda@
        self.fields = ["code",
                       "sg_asset_type",
                       "project",
                       "created_by",
                       "sg_status_list"]
        self.pub_file_ops = pub_file_ops
        self.folder_create_func = create_shotasset
        self.key_values = self.get_entity_key_values()

    def get_entity_key_values(self):
        """Get key values as a dict from self.entity.

        Returns:
            dict
        """
        if self.get_entity_from_event():
            try:
                return {
                    "root": SPIN_ROOT,
                    "division": get_show_division(self.entity["project"]["name"]),
                    "show": self.entity["project"]["name"],
                    "sequence_type": self.sequence_type,
                    "sequence": self.entity["sg_asset_type"],
                    "shot": self.entity["code"],
                    "pipeline_step": "asset",
                    "task_name": "assetusd"
                }
            except KeyError:
                self.logger.error("Failed to get key values of %s", self.type)
        return {}

    def create_work_dir(self):
        """Create work dir from entity properties.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self.folder_create_func(self.key_values)
            return True
        except SystemError as error:
            self.logger.warning("Could not create directory for {}"
                                .format(self.type))
            print(error)
        return False

    def create_root_usda(self):
        """Create root usda file when asset creation happens"""
        os.environ['PROJECT_ROOT'] = \
            os.path.join(self.key_values['root'],
                         self.key_values['division'],
                         self.key_values['show'])
        os.environ['PRODUCTION_TOKEN'] = \
            os.path.join('work', getpass.getuser(), 'staging')
        root_usd_folder = query_path('product_task_name', self.key_values)
        staging_usd_folder = query_path('staging_task_name', self.key_values)
        root_usd_file = os.path.join(root_usd_folder, 'asset_root.usda')
        if os.path.isfile(root_usd_file):
            self.logger.debug("root usd already exists, moving it away")
            staging_usd_file = os.path.join(staging_usd_folder,
                                            'asset_root.usda')
            self.pub_file_ops('-m', 'move', '-s', root_usd_file,
                              '-d', staging_usd_file)
        user = os.getuid()
        temp_folder = os.path.join(staging_usd_folder, 'temp')
        if os.path.isdir(temp_folder):
            self.pub_file_ops('-m', 'rmtree', '-d', temp_folder)
            self.logger.info("temp folder removed")
        self.pub_file_ops('-m', 'mkdir', '-d', temp_folder)
        self.pub_file_ops('-m', 'chown', '-a', user, get_gid('vfx'),
                          '-d', temp_folder)
        asset_root_usd = AssetUsd(os.path.join(temp_folder,
                                               "asset_root.usda"))
        asset_root_usd.add_sublayer(
            os.path.join("${PROJECT_ROOT}", self.key_values['sequence_type'],
                         self.key_values['sequence'],
                         self.key_values['shot'],
                         "${PRODUCTION_TOKEN}/asset/assetusd/${VERSION}/"
                         "layer/usd/asset.usda"),
            production_token='product')
        asset_root_usd.set_default_prim('/asset_' + self.key_values['shot'])
        asset_root_usd.save()
        # clear layer cache in memory
        del asset_root_usd
        self.pub_file_ops('-m', 'move', '-s',
                          os.path.join(temp_folder, "asset_root.usda"),
                          '-d', root_usd_folder)
        self.pub_file_ops('-m', 'rmtree', '-d', temp_folder)
        asset_perm = Permission(444, 'puser', 'pserver')
        self.pub_file_ops('-m', 'chmod', '-a', asset_perm.mod, '-d',
                          root_usd_file)
        self.pub_file_ops('-m', 'chown', '-a', asset_perm.uid,
                          asset_perm.gid, '-d', root_usd_file)

    def publish_asset_first_version(self):
        """Publish first package for asset usd"""
        os.environ['PROJECT_ROOT'] = \
            os.path.join(self.key_values['root'],
                         self.key_values['division'],
                         self.key_values['show'])
        os.environ['PRODUCTION_TOKEN'] = \
            os.path.join('work', getpass.getuser(), 'staging')
        sg_publish_args = {
            'status': 'apr',
            'notes': 'initialize asset usd'
        }
        staging_root = query_path('staging_task_name', self.key_values)
        staging_wip_latest = create_staging_root(self.key_values)
        try:
            os.makedirs(os.path.join(staging_wip_latest, 'layer/usd'))
        except OSError as err:
            self.logger.debug("got error %s creating layer/usd in %s", err,
                              staging_wip_latest)
            self.logger.info("layer/usd already exists!")
        staging_data = [
            'layer/usd/lod_hires.usda',
            'layer/usd/lod_midres.usda',
            'layer/usd/lod_lowres.usda',
            'layer/usd/lod_proxy.usda',
            'layer/usd/asset.usda'
        ]
        tokenized_root = os.path.join(
            "${PROJECT_ROOT}", self.key_values['sequence_type'],
            self.key_values['sequence'], self.key_values['shot'],
            "${PRODUCTION_TOKEN}/asset/assetusd/${VERSION}/")
        # create files in temp folder
        prim_path = '/asset_' + self.key_values['shot']
        component_path = os.path.join(prim_path, 'component')
        assembly_path = os.path.join(prim_path, 'assembly')
        asset_usd = AssetUsd(os.path.join(staging_wip_latest, staging_data[-1]))
        asset_usd.define_prim(prim_path, type_name='Xform')
        asset_usd.define_prim(assembly_path, type_name='Scope')
        asset_usd.override_prim(component_path)
        asset_usd.set_default_prim(prim_path)

        prim = asset_usd.get_prim_at_path(prim_path)
        prim.SetMetadataByDictKey('kind', '', 'assembly')
        component = asset_usd.get_prim_at_path(component_path)
        component.SetMetadataByDictKey('kind', '', 'component')
        assembly = asset_usd.get_prim_at_path(assembly_path)
        assembly.SetMetadataByDictKey('kind', '', 'assembly')

        asset_usd.add_empty_variant_set(prim_path, 'lod')
        for path in staging_data[:-1]:
            lod = path.split('_')[-1].split('.')[0]
            lod_file_path = os.path.join(staging_wip_latest, path)
            lod_usd = AssetUsd(lod_file_path)
            default_prim = '/' + 'asset_' + self.key_values['shot'] + '_' + lod
            component_path = os.path.join(default_prim, 'component')
            lod_usd.define_prim(component_path, type_name='Scope')
            component = lod_usd.get_prim_at_path(component_path)
            component.SetMetadataByDictKey('kind', '', 'component')
            lod_usd.set_default_prim(default_prim)
            lod_usd.save()
            del lod_usd
            lod_tokenized_path = os.path.join(tokenized_root, path)
            self.logger.debug("add reference to lod layer %s for lod %s",
                              lod_tokenized_path, lod)
            asset_usd.add_reference(prim_path, lod_tokenized_path, 'lod',
                                    lod.replace('res', ''),
                                    production_token=
                                    os.path.join('work', getpass.getuser(),
                                                 'staging')
                                   )
        asset_usd.set_variant_selection(prim_path, 'lod', 'hi')
        asset_usd.save()
        del asset_usd
        # publish to product folder
        previous_root, previous_data = None, None
        asset_product_config = level_to_product_config(self.key_values)
        published_paths = asset_product_config.publish(
            self.key_values, self.entity, sg_publish_args,
            staging_wip_latest, staging_data,
            previous_root, previous_data,
            sg=self.sg
        )
        self.pub_file_ops('-m', 'rmtree', '-d', staging_root)
        return published_paths


def registerCallbacks(reg):
    """Register a callback for the event."""
    match_events = {
        "Shotgun_Asset_Change": ["sg_status_list"]
    }

    reg.registerCallback("$ENGINE_SCRIPT_NAME$",
                         "$ENGINE_API_KEY$",
                         create_asset_root,
                         match_events,
                         None,
                         stopOnError=False)

    reg.registerCallback("$ENGINE_SCRIPT_NAME$",
                         "$ENGINE_API_KEY$",
                         update_lod_field,
                         {"Shotgun_Asset_Change": ["sg_publishedpackages"]},
                         None,
                         stopOnError=False)


def create_asset_root(sg, logger, event, _args):
    """When a new asset is created, do invalid char check, if passed, create
    working directory on disk.

    Args:
        sg (object): Shotgun handle.
        logger (object): Spin log handle.
        event (dict): The event caught from event daemon by registerCallbacks.
        _args: Unused but shotgun expects it.

    Returns:
        True is successful, False otherwise.
    """
    pprinter = pprint.PrettyPrinter(indent=4)
    logger.info("Got event in create_asset_root:\n{}\n\n".format(
        pprinter.pformat(event)))

    meta_data = event.get("meta", {})
    try:
        new_value = meta_data["new_value"]
        old_value = meta_data["old_value"]
    except KeyError:
        logger.error("Could not obtain new or old value from event.")
        return False

    # Does not trigger Folder/Network:
    # Not Ready
    # Final
    # On Hold
    # Pinned
    # Omit Omit with Cost
    # N/A
    # Bidding
    #
    # Triggers Folder/Network:
    # Ready to Start
    # In Progress
    # Awaiting Client Feedback
    # Quality Control
    # CBB
    # change list in file /spin/config/SG_plugin_USD/asset_shot_status_list
    valid_old_status = ASSET_STATUS['inactive_status']
    valid_new_status = ASSET_STATUS['active_status']

    if new_value not in valid_new_status or old_value not in valid_old_status:
        logger.info("Not going from inactive status to active status, "
                    "do nothing.")
        return False

    entity = Asset(sg, logger, event)
    entity.get_entity_from_event()

    match = match_invalid_char(entity.get_entity_code())
    if match:
        logger.info("Invalid name for {}: '{}' in show '{}' caught."
                    "".format(entity.entity["type"],
                              entity.entity["code"],
                              entity.entity["project"]["name"]))

        email_list = entity.get_email_lists()
        notify_invalid_name(sg, entity, email_list, logger, match)

    else:
        if entity.create_work_dir():
            logger.info("Asset dir created for asset {} in project {}.".format(
                entity.entity["code"], entity.entity["project"]["name"]))
            if entity.entity["project"]["name"] in SELECTED_SHOW:
                logger.info("Creating root usda files")
                entity.publish_asset_first_version()
                entity.create_root_usda()
            return True
    return False


def update_lod_field(sg, logger, event, _args):
    """update asset sg_lod_list field from model package"""
    pprinter = pprint.PrettyPrinter(indent=4)
    logger.info("Got event in update_lod_field:\n{}\n\n".format(
        pprinter.pformat(event)))
    try:
        meta = event["meta"]
        asset = event["entity"]
        added_pp = meta.get("added")
    except KeyError:
        logger.error("Failed to get one or more of metadata, asset entity,"
                     " and added list from event")
        return False
    if added_pp:
        model_pp = []
        for publish_package in added_pp:
            if publish_package["name"].startswith("model"):
                model_pp.append(publish_package)
    if not model_pp:
        logger.info("No model package attached, skip.")
        return True
    lod_list = get_lod_list(sg, model_pp)
    lod_string = ", ".join(lod_list)
    logger.info("Update Asset %s lod list with: %s", asset["name"], lod_list)
    return sg.update("Asset", asset["id"], {'sg_lod_list': lod_string})
