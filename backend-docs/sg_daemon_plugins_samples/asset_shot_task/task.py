"""
Observe when a task name has been changed and do name check. Roll the name back
if illegal.
"""
from __future__ import print_function  # fix pylint

import os
import re
import pprint
import copy
from abc import ABCMeta, abstractmethod

import emailutil

from spin_config_manager.config_manager import SpinResolvedConfig

from spin_file_system.products import (
    sync_latest_product_to_staging,
    level_to_product_config,
    get_latest_product_path
)
from spin_file_system.constants import SPIN_ROOT
from spin_file_system.directories import create_staging_root
from spin_file_system.utility import get_show_division

from spin_usd_util.usd_api import UsdFile, AssetUsd

PACKAGE_ROOT = '/'.join(os.path.realpath(__file__).split('/')[:-3])
CALENDAR_SCRIPT = os.path.join(PACKAGE_ROOT, 'bin/google_calendar.sh')
with open("/spin/share/Projects/pipeline/szhang/"
          "spin_calender/scanning/calendar_id.txt", "r") as calendar_file:
    SCANNING_CALENDAR_ID = calendar_file.readline().split("\n")[0]

SELECTED_SHOW = dict(SpinResolvedConfig('usd_show.json',
                                        subdirs='SG_plugin_USD',
                                        merge=True, ))['show']

PIPELINE_STEP_STACK = dict(SpinResolvedConfig('pipeline_step_stack.json',
                                              subdirs='SG_plugin_USD',
                                              merge=True, ))

TASK_STATUS = dict(SpinResolvedConfig('asset_shot_status_list.json',
                                      subdirs='SG_plugin_USD',
                                      merge=True,))['task_status']


def _index_less_than(order, left, right):
    """Compare the pipeline step order.

    Args:
        order (list): list of items
        left (obj): left item
        right (obj): right item

    Returns:
        True if left has lesser index than right, False otherwise
    """
    if not order:
        return False
    try:
        left_idx = order.index(left)
    except ValueError:
        # left not in list, so it has index at infinity
        return False
    try:
        right_idx = order.index(right)
    except ValueError:
        # right not in list, so it has index at infinity
        return True
    return left_idx < right_idx


def task_key_less_than(entity_type, left, right):
    """Compare pipeline_step and task_name based on config

    Args:
        entity_type (text): 'asset' or 'shot'
        task (str, str): tuple of pipeline_step, task_name
        other (str, str): tuple of pipeline_step, task_name to compare against

    Returns:
        True if task is preferred over other
    """
    if left[0] != right[0]:
        return _index_less_than(
            PIPELINE_STEP_STACK.get('{}_steps'.format(entity_type)),
            left[0], right[0]
        )
    return _index_less_than(
        PIPELINE_STEP_STACK[entity_type].get(left[0]),
        left[1], right[1]
    )


def get_task_insert_index(asset_path_list, entity_type,
                          pipeline_step, task_name,
                          is_variant=False):
    """Derive index to insert new sublayer at

    Args:
        asset_path_list (list): existing list of paths
        entity_type (str): entity type (asset|shot)
        pipeline_step (str): sublayer pipeline step
        task_name (str): sublayer task name
        is_variant (bool): treat task from path list as a variant

    Return:
        index to insert at
    """
    if not asset_path_list:
        return 0

    current_key = (pipeline_step, task_name)
    task_key_list = []
    for path in asset_path_list:
        relative_path = path.split('${PRODUCTION_TOKEN}/')[-1]
        step, task = relative_path.split('/${VERSION}')[0].split('/')
        if is_variant:
            name_parts = task.split('_')
            if len(name_parts) > 1:
                task = '_'.join(name_parts[:-1])
        task_key_list.append((step, task))

    for idx, task_key in enumerate(task_key_list):
        if task_key_less_than(entity_type, current_key, task_key):
            return idx

    return len(asset_path_list)


INVALID_CHAR = re.compile(r'\W')  # pylint: disable=anomalous-backslash-in-string


def match_invalid_char(name):
    """Check if there is invalid character in string.

    Args:
        name (str): string of the name to be checked.

    Returns:
        object: Match object which contain result of check, None if no invalid
            char or none string name received.
    """
    if isinstance(name, str):
        return INVALID_CHAR.search(name)
    return None


def assert_variant_set(name, illegal=('asset_variant',)):
    """Check if the given name is a valid string, return the string if it is
    valid and None otherwise

    Args:
        name (str): string of the name to be checked.

    Returns:
        valid string or None
    """
    if name in illegal:
        return None
    if isinstance(name, str):
        name = name.strip()
        if not INVALID_CHAR.search(name):
            return name
    return None


def notify_invalid_name(sg, entity, email_list, logger, match):
    """
    Email creator and cc producers that an invalid name is detected and status
     of the entity is set to N/A.

    Args:
        sg (object): Shotgun connection.
        entity (Entity): Task entity instance.
        email_list (Tuple[list, list]): List of two lists, first is msg_to_list, second is
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
        return None
    if not emailutil.send_email(
            emailutil.SPIN_EMAIL_HOST, emailutil.SPIN_EMAIL_PORT,
            "noreply@shotgunstudio.com",
            email_list[0],
            "Invalid name for new {}: '{}' in show '{}'"
            "".format(entity.entity["type"],
                      entity.entity["code"],
                      entity.entity["project"]["name"]),
            "Hello {3},\n\n"
            "Name could not contain characters other than"
            " a-z, A-z, 0-9 and '_'.\n"
            "The first invalid character: '{0}'.\n"
            "We'd suggest you set the task in Shotgrid to N/A status and "
            "remake a new asset without the invalid characters.\n\n"
            "All producers have been notified. "
            "For more information, click this {entity_type} webpage: "
            "https://spinvfx{1}.shotgunstudio.com/detail/{entity_type}/{2}\n\n"
            "- SG Daemon Plugin"
            "".format(match.group(),
                      server,
                      entity.entity["id"],
                      entity.event["user"]["name"],
                      entity_type=entity.entity["type"]),
            msg_cc_list=email_list[1]):
        logger.warning("Failed to send emails")
        return None
    return True


def notify_invalid_change(sg, entity, email_list, logger, match):
    """
    Email creator that an invalid new name is detected and entity name is rolled
    back.

    Args:
        sg (object): Shotgun connection.
        entity (Entity): Task entity instance.
        email_list (Tuple[list, list]): List of two lists, first is msg_to_list, second is
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
        return None
    if not emailutil.send_email(
            emailutil.SPIN_EMAIL_HOST, emailutil.SPIN_EMAIL_PORT,
            "noreply@shotgunstudio.com",
            email_list[0],
            "Invalid name change for {}: '{}' in show '{}'"
            "".format(entity.entity["type"],
                      entity.entity["code"],
                      entity.entity["project"]["name"]),
            "Name could not contain characters other than "
            "a-z, A-z, 0-9 and '_'.\n"
            "The first invalid character: '{0}'.\n"
            "Name of {entity_type} rolled back!\n"
            "For more information, check {entity_type} webpage: "
            "https://spinvfx{1}.shotgunstudio.com/detail/{entity_type}/{2}"
            "".format(match.group(),
                      server,
                      entity.entity["id"],
                      entity_type=entity.entity["type"]), ):
        logger.warning("Failed to send emails")
        return None
    return True


def check_user_status(sg, logger, human_user):
    """Check if the HumanUser is still active.

    Args:
        sg (object): Shotgun connection.
        logger (object): Logger handle.
        human_user (dict): HumanUser dict which should as least provide shotgun
            id of the user in key 'id'.

    Returns:
        True if active, False if not active or no 'id' found in human_user.
    """
    if "status" in human_user:
        if human_user["status"] == "act":
            return True
        return False
    if "sg_status_list" in human_user:
        if human_user["sg_status_list"] == "act":
            return True
        return False
    try:
        user = sg.find("HumanUser", [["id", "is", human_user["id"]]],
                       ["sg_status_list"])
        if user["sg_status_list"] == "act":
            return True
    except KeyError:
        logger.warning("Please include 'id' for human_user")
    return False


def resolve_extension(basename, extensions):
    """Check a given filepath with each extension and return the first path that exists

    Args:
        basename (str): path without extension
        extensions (list): list of extensions to try

    Raises:
        OSError if file not found with any extension

    Returns:
        valid path
    """
    for ext in extensions:
        path = '.'.join((basename, ext))
        if os.path.isfile(path):
            return path
    raise OSError('File not found: {!r} {!r}'.format(basename, extensions))


def get_task_product(task_entity, event, logger, sg):
    """ Try to get task, key values and products.

    Args:
        task_entity (object): Task instance
        event (dict): event dict
        logger: logger handle
        sg: sg instance

    Returns:
        True is successful, False otherwise.

    """
    if not task_entity.get_entity_from_event():
        logger.error("Could not obtain task entity from event.")
        return False
    match = match_invalid_char(task_entity.entity["code"])
    if match and not event["meta"].get("in_create"):
        email_list = task_entity.get_email_lists()
        notify_invalid_name(sg, task_entity, email_list, logger, match)
        logger.error("Invalid name for {}: '{}' caught."
                     .format(task_entity.entity["type"], task_entity.entity["code"]))
        return False
    if not task_entity.get_entity_key_values():
        logger.error("Could not obtain level information for current task or "
                     "attached shot/asset")
        return False
    if not task_entity.get_product_configs():
        logger.info("No product found for current task, skipping.")
        return False
    return True


class Entity:  # pylint: disable=too-many-instance-attributes
    """Shot grid entity, inherited by asset, shot or task.
    Attributes:
        fields (list of str): Fields to find in shotgun, to be defined in
            instances.
        type (str): Entity type. (asset, shot or task)
        dirutil_func (object): Function to be imported from dirutil to do
            directory creation.
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
        self.dirutil_func = None

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
        producer_list = self.get_producer_list_from_project_id(
            self.entity["project"]["id"])

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

    def get_producer_list_from_project_id(self,  # pylint: disable=invalid-name
                                          project_id):
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


class Task(Entity):  # pylint:disable=too-many-instance-attributes
    """Shotgun task entity.

    Attributes:
        fields (list of str): Fields to find in shotgun.
        type (str): Entity type. (asset, shot or task)
    """

    def __init__(self, sg, logger, event):
        super(Task, self).__init__(sg, logger, event)
        self.staging_wip_latest = None
        self.type = "Task"
        self.fields = ["content",
                       "project",
                       "created_by",
                       "entity",
                       "step",
                       "start_date",
                       "due_date",
                       "sg_task_description",
                       "task_assignees",
                       "sg_status_list",
                       "sg_variant_set"]
        self.sequence_type = ''
        self.attach_entity = {}
        self.task_key_values = {}
        self.attached_entity_key_values = {}
        self.product_config = None
        self.product_asset = None

    def get_entity_from_id(self, entity_id):
        """Get entity dict from entity id, need to define self.type and
        self.field first.
        Overriding the method of Class Entity. Since task entity has it's name
        under key 'content' instead pf 'code'.

        Args:
            entity_id (str): Shotgun entity id.

        Returns:
            Dict of entity found in shotgun.
        """
        filters = [["id", "is", entity_id]]
        entity = self.sg.find_one(self.type, filters, self.fields)

        if not entity:
            self.logger.warning("Could not obtain {} with {} ID {}"
                                .format(self.type, self.type, entity_id))
            return None

        # Copying this to use the same email code from shot.py in class entity
        entity["code"] = entity["content"]

        return entity

    def get_staging_data(self):
        """get file lod and staging file lists and return in a dict

        Returns:

        """
        staging_data = {
            'lod': [],
            'layer': []
        }
        if self.product_config.lod:
            for lod_layer in self.product_config.lod.values():
                if 'usda' in lod_layer.ext:
                    lod_layer_file = lod_layer.name + '.usda'
                    staging_data['lod'].append(lod_layer_file)
        if self.product_config.layer:
            layer = self.product_config.layer
            if 'usda' in layer.ext:
                layer_file = layer.name + '.usda'
                staging_data['layer'].append(layer_file)
        return staging_data

    def publish_task_package(self):
        """publish task package to publish folder

        Returns:

        """
        if os.path.isdir(get_latest_product_path(self.task_key_values)):
            self.logger.info("Task package existed, skip publishing")
            return True
        entity_type = self.entity['entity']['type'].lower()
        sg_publish_args = {
            'status': 'apr',
            'notes': 'new task package'
        }
        sg_task = self.entity
        if not self.staging_wip_latest:
            self.staging_wip_latest = create_staging_root(self.task_key_values)
        try:
            os.makedirs(os.path.join(self.staging_wip_latest, 'layer/usd'))
        except OSError:
            self.logger.info("layer/usd already exists!")
        second_level_prim = {
            'lod': 'component',
            'layer': 'assembly'
        }
        staging_data = self.get_staging_data()
        prim_path_root = '/' + entity_type + '_' + self.task_key_values["shot"]
        for key, staging_list in staging_data.items():
            for path in staging_list:
                if key == 'lod':
                    lod = path.split('_')[-1].split('.')[0]
                    prim_path = prim_path_root + '_' + lod
                else:
                    prim_path = prim_path_root
                usd_file_path = os.path.join(self.staging_wip_latest, path)
                usd_file = UsdFile(usd_file_path)
                usd_file.define_prim(prim_path, type_name='Xform')
                if entity_type == 'asset':
                    component_path = \
                        os.path.join(prim_path, second_level_prim[key])
                    usd_file.define_prim(component_path,
                                         type_name='Scope')
                    component = usd_file.get_prim_at_path(component_path)
                    component.SetMetadataByDictKey(
                        'kind', '', second_level_prim[key]
                    )
                usd_file.set_default_prim(prim_path)
                usd_file.set_asset_info(prim_path,
                                        {'task_id': self.entity['id']})
                usd_file.save()
                del usd_file
        staging_data = staging_data['lod'] + staging_data['layer']
        previous_root, previous_data = None, None
        self.logger.info("Publishing %s", str(staging_data))
        published_result = self.product_config.publish(
            self.task_key_values, sg_task, sg_publish_args,
            self.staging_wip_latest, staging_data,
            previous_root, previous_data,
            sg=self.sg
        )
        self.logger.info("Task package published.")
        return published_result

    def publish_attached_entity(self):
        """

        Returns:

        """
        entity_type = self.attached_entity_key_values['pipeline_step']
        attached_product_config = \
            level_to_product_config(self.attached_entity_key_values)
        staging_data = [
            'layer/usd/' + entity_type + '.usda'
        ]
        if entity_type == 'asset':
            staging_data.extend(
                ['layer/usd/lod_hires.usda',
                 'layer/usd/lod_midres.usda',
                 'layer/usd/lod_lowres.usda',
                 'layer/usd/lod_proxy.usda'])

        sg_publish_args = {
            'status': 'apr',
            'notes': 'initialize asset usd'
        }
        previous_root, previous_data = None, None
        published_paths = attached_product_config.publish(
            self.attached_entity_key_values, self.entity['entity'],
            sg_publish_args, self.staging_wip_latest, staging_data,
            previous_root, previous_data,
            sg=self.sg
        )
        return bool(published_paths)

    def get_attached_entity_properties(self):
        """Get propertied from the shot/asset entity attached in 'entity' field
         of the task"""
        if not self.entity:
            self.get_entity_from_event()
        try:
            entity_type = self.entity['entity']['type']
            entity_id = self.entity['entity']['id']
        except (KeyError, TypeError):
            return None
        if entity_type == 'Asset':
            entity_field = ["code", "sg_asset_type", "project", "created_by"]
            self.attach_entity = self.sg.find_one(entity_type,
                                                  [['id', 'is', entity_id]],
                                                  entity_field)
            self.sequence_type = 'asset'
            return True
        elif entity_type == 'Shot':
            entity_field = ["code", "sg_sequence", "project", "created_by"]
            self.attach_entity = self.sg.find_one(entity_type,
                                                  [['id', 'is', entity_id]],
                                                  entity_field)
            self.sequence_type = 'sequence'
            return True
        self.logger.warning("Task has no asset or shot attached!")
        return False

    def get_entity_key_values(self):
        """Get key values as a dict from self.entity.

        Returns:
            dict
        """
        if self.get_entity_from_event() and \
                self.get_attached_entity_properties():
            try:
                self.task_key_values = {
                    "root": SPIN_ROOT,
                    "division": get_show_division(self.entity["project"]["name"]),
                    "show": self.entity["project"]["name"],
                    "sequence_type": self.sequence_type,
                    "sequence":
                        self.attach_entity["sg_asset_type"] if
                        self.entity['entity']['type'] == "Asset" else
                        self.attach_entity["sg_sequence"]["name"],
                    "shot": self.attach_entity["code"],
                    "pipeline_step": self.entity["step"]["name"],
                    "task_name": self.entity["code"]
                }
                self.attached_entity_key_values = copy.deepcopy(
                    self.task_key_values)
                self.attached_entity_key_values.update(
                    {
                        "pipeline_step": self.entity['entity']['type'].lower(),
                        "task_name": self.entity['entity']['type'].lower() + 'usd'
                    }
                )
                return True
            except (KeyError, TypeError):
                self.logger.error("Failed to get key values of %s", self.type)
        return False

    def get_product_configs(self):
        """

        Returns:

        """
        if self.task_key_values:
            try:
                self.product_config = \
                    level_to_product_config(self.task_key_values)
            except ValueError as err:
                self.logger.warning("%s", str(err))
                return False

        if self.attached_entity_key_values:
            try:
                self.product_asset = \
                    level_to_product_config(self.attached_entity_key_values)
            except ValueError as err:
                self.logger.warning("%s", str(err))
                return False
        return True

    def setup_asset_shot_usd_for_editing(self):
        """Setup the staging area for editing shot/asset usd. Derive
        dict of target_usd -> payload_file_path.

        Returns:
            edit targets, or False if no edit is needed.
        """
        if not self.product_config.layer and not self.product_config.lod:
            # nothing to add/remove
            return False

        sync_latest_product_to_staging(self.attached_entity_key_values)
        self.staging_wip_latest = create_staging_root(self.attached_entity_key_values)
        self.logger.info("staging: {}".format(self.staging_wip_latest))

        os.environ['PROJECT_ROOT'] = \
            os.path.join(self.task_key_values['root'],
                         self.task_key_values['division'],
                         self.task_key_values['show'])
        os.environ['PRODUCTION_TOKEN'] = 'product'
        return self.derive_edit_targets()

    def derive_edit_targets(self, level=None):
        """Derive dict of target_usd -> payload_file_path.

        Returns:
            edit targets, or False if no edit is needed.
        """
        if level is None:
            level = self.task_key_values
            product_config = self.product_config
        else:
            product_config = level_to_product_config(level)
        edit_targets = {}
        if product_config.lod and self.product_asset.lod:
            for resolution, asset_payload in self.product_asset.lod.items():
                if resolution not in product_config.lod:
                    continue
                try:
                    target = resolve_extension(
                        os.path.join(self.staging_wip_latest,
                                     asset_payload.name),
                        asset_payload.ext
                    )
                except OSError:
                    continue
                edit_targets[target] = product_config.lod[resolution]\
                    .tokenized_path(level)
        if product_config.layer and self.product_asset.layer:
            asset_usd_payload = self.product_asset.\
                payloads['layer']
            try:
                target = resolve_extension(
                    os.path.join(self.staging_wip_latest,
                                 asset_usd_payload.name),
                    asset_usd_payload.ext
                )
            except OSError:
                return False
            edit_targets[target] = product_config.layer.tokenized_path(level)
        return edit_targets

    def update_asset_shot_status(self, insert=True):
        """Update asset/shot usd file in publish folder

        Args:
            insert (bool): if true, the product is inserted (inactive -> active)
                otherwise it is removed (active -> inactive)

        Returns:
            True if published
        """
        # if sg_variant_set has value, use the variant update workflow
        variant_set = assert_variant_set(self.entity.get('sg_variant_set'))
        if variant_set:
            if insert:
                return self.update_asset_shot_variant(
                    None, variant_set, sublayer=False
                )
            return self.update_asset_shot_variant(
                variant_set, None, sublayer=False
            )

        # standard case
        edit_targets = self.setup_asset_shot_usd_for_editing()
        if not edit_targets:
            return False

        if insert:
            for target, file_path in edit_targets.items():
                self.logger.info('Update %r', target)
                layer = AssetUsd(target)
                insert_index = get_task_insert_index(
                    layer.sublayer,
                    self.attached_entity_key_values["pipeline_step"],
                    self.task_key_values["pipeline_step"],
                    self.task_key_values["task_name"]
                )
                self.logger.info('Insert sublayer %r (idx %r)', file_path, insert_index)
                layer.insert_sublayer(file_path, insert_index)
                layer.save()
        else:
            for target, file_path in edit_targets.items():
                self.logger.info('Update %r', target)
                layer = AssetUsd(target)
                self.logger.info('Remove sublayer %r', file_path)
                layer.remove_sublayer(file_path)
                layer.save()

        return self.publish_attached_entity()

    def update_asset_shot_task_name(self, old_task_name):
        """Update asset/shot usd file in publish folder when task name changed

        Args:
            old_task_name (str): old task name
            new_task_name (str): new variant set name or None

        Returns:
            True if published
        """
        new_edit_targets = self.setup_asset_shot_usd_for_editing()
        old_level = dict(self.task_key_values)
        old_level['task_name'] = old_task_name
        old_edit_targets = self.derive_edit_targets(old_level)

        if not old_edit_targets and not new_edit_targets:
            return False

        variant_set = assert_variant_set(self.entity.get('sg_variant_set'))

        if old_edit_targets:
            if variant_set:
                for target_usd, payload_file_path in old_edit_targets.items():
                    self.update_layer_variant(
                        target_usd, payload_file_path,
                        variant_set, None,
                        self.attached_entity_key_values['pipeline_step'],
                        old_level['pipeline_step'],
                        old_task_name,
                        sublayer=False
                    )
            else:
                for target_usd, payload_file_path in old_edit_targets.items():
                    self.logger.info('Update %r', target_usd)
                    layer = AssetUsd(target_usd)
                    self.logger.info('Remove sublayer %r', payload_file_path)
                    layer.remove_sublayer(payload_file_path)
                    layer.save()

        if new_edit_targets:
            self.publish_task_package()
            if variant_set:
                for target_usd, payload_file_path in new_edit_targets.items():
                    self.update_layer_variant(
                        target_usd, payload_file_path,
                        None, variant_set,
                        self.attached_entity_key_values['pipeline_step'],
                        self.task_key_values['pipeline_step'],
                        self.task_key_values['task_name'],
                        sublayer=False
                    )
            else:
                for target_usd, payload_file_path in new_edit_targets.items():
                    self.logger.info('Update %r', target_usd)
                    layer = AssetUsd(target_usd)
                    insert_index = get_task_insert_index(
                        layer.sublayer,
                        self.attached_entity_key_values["pipeline_step"],
                        self.task_key_values["pipeline_step"],
                        self.task_key_values["task_name"]
                    )
                    self.logger.info(
                        'Insert sublayer %r (idx %r)',
                        payload_file_path, insert_index
                    )
                    layer.insert_sublayer(payload_file_path, insert_index)
                    layer.save()

        return self.publish_attached_entity()

    def update_asset_shot_variant(self, old_variant_set, new_variant_set,
                                  sublayer=True):
        """Update asset/shot usd file in publish folder when variant set name
        is changed, or when task with variant set becomes active/inactive

        Args:
            old_variant_set (str|None): old variant set name or None
            new_variant_set (str|None): new variant set name or None
            sublayer (bool): if true, add removed variants as sublayer

        Returns:
            True if published
        """
        edit_targets = self.setup_asset_shot_usd_for_editing()
        if not edit_targets:
            return False

        for target_usd, payload_file_path in edit_targets.items():
            self.update_layer_variant(
                target_usd, payload_file_path,
                old_variant_set, new_variant_set,
                self.attached_entity_key_values['pipeline_step'],
                self.task_key_values['pipeline_step'],
                self.task_key_values['task_name'],
                sublayer=sublayer
            )

        return self.publish_attached_entity()

    def update_layer_variant(self, target_usd, payload_file_path, # pylint: disable=too-many-branches, too-many-arguments
                             old_variant_set, new_variant_set,
                             entity_type, pipeline_step, task_name,
                             sublayer=True):
        """Update variants for a given layer"""
        self.logger.info('Updating %s', target_usd)
        self.logger.info('Set %s/%s variant set to %r (was %r)',
                         pipeline_step, task_name,
                         new_variant_set, old_variant_set)

        layer = AssetUsd(target_usd)
        prim_path = str(layer.get_default_prim().GetPath())

        variant, ordering_task_name =\
            self.product_config.get_variant_name(task_name)

        self.logger.info('Variant name %r', variant)

        if old_variant_set is not None:
            old_variants = layer.get_variants(prim_path, old_variant_set)
            if variant in old_variants:
                layer.remove_reference(
                    prim_path, payload_file_path,
                    v_set_name=old_variant_set, variant=variant
                )
                if not layer.get_reference(
                        prim_path, v_set_name=old_variant_set, variant=variant
                    ):
                    self.logger.info('Remove variant %r from %r (%s)',
                                     variant, old_variant_set, prim_path)
                    if len(old_variants) == 1:
                        layer.remove_variant_set(prim_path, old_variant_set)
                    else:
                        layer.remove_variant(
                            prim_path, old_variant_set, (variant,)
                        )
        elif sublayer and payload_file_path in layer.sublayer:
            self.logger.info('Remove sublayer %r', payload_file_path)
            layer.remove_sublayer(payload_file_path)

        if new_variant_set is not None:
            new_variants = layer.get_variants(prim_path, new_variant_set)
            if variant not in new_variants:
                self.logger.info('Add variant %r to %r (%s)',
                                 variant, new_variant_set, prim_path)
                layer.add_variant(prim_path, new_variant_set, (variant,))
            insert_index = get_task_insert_index(
                layer.get_reference(
                    prim_path, v_set_name=new_variant_set, variant=variant
                ), entity_type, pipeline_step, ordering_task_name,
                is_variant=True
            )
            self.logger.info(
                'Insert reference %r (index %d)',
                payload_file_path, insert_index
            )
            layer.insert_reference(
                prim_path, payload_file_path, insert_index,
                v_set_name=new_variant_set,
                variant=variant
            )
            layer.set_variant_selection(prim_path, new_variant_set, variant)
        elif sublayer and not payload_file_path in layer.sublayer:
            self.logger.info('Add sublayer %s', payload_file_path)
            insert_index = get_task_insert_index(
                layer.sublayer, entity_type,
                pipeline_step, ordering_task_name
            )
            layer.insert_sublayer(payload_file_path, insert_index)

        layer.save()

    def get_summary_and_description(self):
        """Get summary and description for calendar event from task description.
        """
        if self.entity["description"]:
            description_split = self.entity["description"].split("-")
            if len(description_split) == 1 or len(description_split[0]) > 2:
                if not description_split[0] == "on" or \
                        description_split[0] == "ON":
                    title = '-'.join(description_split[0:2])
                else:
                    title = description_split[0]
                description = "\n".join(description_split[1:]) if \
                    len(description_split) > 1 else ""
            else:
                title = "-".join(description_split[0:2])
                description = "\n".join(description_split[2:])
            summary = "[{}]_{}_{}".format(self.entity["project"]["name"],
                                          title,
                                          self.entity["task_id"])
            return summary, description
        return None


def registerCallbacks(reg):
    """Register a callback for the event."""
    name_check_event = {
        "Shotgun_Task_Change": ["content"]
    }

    reg.registerCallback("$ENGINE_SCRIPT_NAME$",
                         "$ENGINE_API_KEY$",
                         task_name_change,
                         name_check_event,
                         None,
                         stopOnError=False)

    usd_update_event = {
        "Shotgun_Task_Change": ["sg_status_list"]
    }

    reg.registerCallback("$ENGINE_SCRIPT_NAME$",
                         "$ENGINE_API_KEY$",
                         task_update_usd,
                         usd_update_event,
                         None,
                         stopOnError=False)

    variant_update_event = {
        "Shotgun_Task_Change": ["sg_variant_set"]
    }
    reg.registerCallback("$ENGINE_SCRIPT_NAME$",
                         "$ENGINE_API_KEY$",
                         task_update_variant,
                         variant_update_event,
                         None,
                         stopOnError=False)


def task_name_change(sg, logger, event, _args):  # pylint: disable=too-many-return-statements
    """Check if the new name of a name changing event is legal.
    If not, roll the name back and notify creator.

    Args:
        sg (object): Shotgun handle.
        logger (object): Spin log handle.
        event (dict): The event caught from event daemon by registerCallbacks.
        _args: Unused but shotgun expects it.

    Returns:
        True is successful, False otherwise.
    """
    # TODO: check task naming convention with config files
    pprinter = pprint.PrettyPrinter(indent=4)
    logger.info("Got event in check_updated_name:\n\n{}\n\n"
                .format(pprinter.pformat(event)))
    old_name = event["meta"]["old_value"]
    new_name = event["meta"]["new_value"]
    try:
        get_show_division(event["project"]["name"])
    except (ValueError, TypeError):
        logger.info("Not a active show!. Skipping")
        return False
    if new_name:
        match = match_invalid_char(new_name)
        if match:
            entity = Task(sg, logger, event)
            if entity.get_entity_from_event():
                logger.info("Invalid name change for {}: '{}' caught, "
                            "old name: '{}'".format(entity.entity["type"],
                                                    entity.entity["code"],
                                                    old_name))
                email_list = entity.get_email_lists()
                # if task name is invalid
                if not event["meta"].get("in_create"):
                    # if it's not a newly created task, try to revert task name
                    if not match_invalid_char(old_name):
                        # if old name is valid, revert name and notify change
                        sg.update(entity.entity["type"],
                                  entity.entity["id"],
                                  {"content": old_name})
                        notify_invalid_change(
                            sg, entity, email_list, logger, match
                        )
                        return False
                    else:
                        # if old name is invalid, log it and notify invalid name
                        logger.info("Old name also invalid")
                # if it's a new task or old name is invalid, notify invalid name
                notify_invalid_name(sg, entity, email_list, logger, match)
            return False

    else:
        logger.info("Task new name is None!")
        return False

    if event["meta"].get("in_create"):
        #  new task with valid name,
        #  don't do asset/shot usd update since it's new
        return True
    # name is valid, perform asset/shot usd update
    entity = Task(sg, logger, event)
    if not get_task_product(entity, event, logger, sg):
        return False
    if entity.entity['sg_status_list'] not in TASK_STATUS["active_status"]:
        return False
    if not entity.entity["project"]["name"] in SELECTED_SHOW:
        return False
    return entity.update_asset_shot_task_name(old_name)


def task_update_usd(sg, logger, event, _args):  # pylint: disable=too-many-return-statements,too-many-branches
    """Update related usd file with received task.

    Args:
        sg (object): Shotgun handle.
        logger (object): Spin log handle.
        event (dict): The event caught from event daemon by registerCallbacks.
        _args: Unused but shotgun expects it.

    Returns:
        True is successful, False otherwise.

    """
    # TODO: filter tasks that are belonged to a active film/television project
    pprinter = pprint.PrettyPrinter(indent=4)
    logger.info("Got event in task_update_usd:\n{}\n\n".format(
        pprinter.pformat(event)))
    try:
        get_show_division(event["project"]["name"])
    except (ValueError, TypeError):
        logger.info("Not a active show!. Skipping")
        return False
    if not event["project"]["name"] in SELECTED_SHOW:
        logger.info("show {} not in usd_selected_show list {}".
                    format(event["project"]["name"],
                           str(SELECTED_SHOW)))
        return False
    meta_data = event.get("meta", {})
    try:
        new_value = meta_data["new_value"]
        old_value = meta_data["old_value"]
    except KeyError:
        logger.error("Could not obtain new or old value from event.")
        return False
    inactive_status = TASK_STATUS["inactive_status"]
    active_status = TASK_STATUS["active_status"]

    entity = Task(sg, logger, event)
    if not get_task_product(entity, event, logger, sg):
        return False

    if new_value in active_status and old_value in inactive_status:
        logger.info("Going from inactive status to active status.")
        if entity.publish_task_package():
            if entity.update_asset_shot_status():
                logger.info("Asset/Shot usd updated, "
                            "assetusd/shotusd package published.")
                return True
            logger.error("Failed to publish task package.")
            return False
        logger.error("Failed to update asset/shot usd.")
        return False

    if new_value in inactive_status and old_value in active_status:
        logger.info("Going from active status to inactive status.")
        entity.update_asset_shot_status(insert=False)
        return True
    return False


def task_update_variant(sg, logger, event, _args):
    """Update asset shot variants when sg_variant_set is changed

    Args:
        sg (object): Shotgun handle.
        logger (object): Spin log handle.
        event (dict): The event caught from event daemon by registerCallbacks.
        _args: Unused

    Returns:
        True is successful, False otherwise.
    """
    pprinter = pprint.PrettyPrinter(indent=4)
    logger.info("Got event in task_update_variant:\n{}\n\n".format(
        pprinter.pformat(event)))
    meta_data = event.get("meta", {})
    try:
        new_value = assert_variant_set(meta_data["new_value"])
        old_value = assert_variant_set(meta_data["old_value"])
    except KeyError:
        logger.error("Could not obtain new or old value from event.")
        return False

    if not new_value and not old_value:
        return False

    entity = Task(sg, logger, event)
    if new_value not in TASK_STATUS["active_status"]:
        return False
    if not event["project"]["name"] in SELECTED_SHOW:
        return False
    if not get_task_product(entity, event, logger, sg):
        return False

    return entity.update_asset_shot_variant(old_value, new_value)
