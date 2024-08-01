"""version (Version and PublishedFile) status cascade to upstream candidates."""

VERSION_ENTITY_VERSION = 'Version'
VERSION_ENTITY_PUBLISHED_FILE = 'PublishedFile'
VERSION_ENTITY_PUBLISHED_PACKAGE = 'CustomEntity01'
VERSION_ENTITY_TYPES = [VERSION_ENTITY_VERSION, VERSION_ENTITY_PUBLISHED_FILE,
                        VERSION_ENTITY_PUBLISHED_PACKAGE]


def registerCallbacks(reg):
    """Register callbacks."""

    for entity_type in VERSION_ENTITY_TYPES:
        match_events = {'Shotgun_%s_Change' % entity_type: ['sg_status_list']}
        reg.registerCallback(
            '$ENGINE_SCRIPT_NAME$', '$ENGINE_API_KEY$',
            handle_version_status_change, match_events, None, stopOnError=False
        )


def form_updates(sg, log, sg_entity):
    """Form the updates list for given sg entity."""

    # query the upstream_candidates multi-entity fields. see also sg2003, we needed
    # to shorten the names for shotgun's sake.
    if sg_entity['type'] == VERSION_ENTITY_PUBLISHED_FILE:
        task_field = 'task'
    else:
        task_field = 'sg_task'
    fields = ['sg_status_list', 'sg_ups_candidates_pf',
              'sg_ups_candidates_v', 'sg_publishedpackges', 'sg_published_files'
              , task_field]
    sg_entity = sg.find_one(
        sg_entity['type'],
        [['id', 'is', sg_entity['id']]],
        fields
    )
    tech_check_task = sg_entity[task_field]

    # let's avoid setting status on upstream candidates if they are already in that
    # status.  this is a slight defense against loops in this graph.
    upstream_candidates_pfs_ids = [
        upstream_entity['id'] for upstream_entity in
        sg_entity.get('sg_ups_candidates_pf', [])
    ]
    published_file_ids = [
        published_files['id'] for published_files in
        sg_entity.get('sg_published_files', [])
    ]
    upstream_candidates_pfs_ids = upstream_candidates_pfs_ids + \
                                  published_file_ids
    published_files = []
    if upstream_candidates_pfs_ids:
        published_files = sg.find(
            VERSION_ENTITY_PUBLISHED_FILE,
            [['id', 'in', upstream_candidates_pfs_ids]],
            ['sg_status_list', 'task']
        )
        for published_file in published_files:
            published_file['sg_task'] = published_file['task']

    upstream_candidates_vs_ids = [
        upstream_entity['id'] for upstream_entity in
        sg_entity.get('sg_ups_candidates_v', [])
    ]
    upstream_candidates_vs = []
    if upstream_candidates_vs_ids:
        upstream_candidates_vs = sg.find(
            VERSION_ENTITY_VERSION,
            [['id', 'in', upstream_candidates_vs_ids]],
            ['sg_status_list', 'sg_task']
        )

    published_package_ids = [
        published_package['id'] for published_package in
        sg_entity.get('sg_publishedpackges', [])
    ]
    published_packages = []
    if published_package_ids:
        published_packages = sg.find(
            VERSION_ENTITY_PUBLISHED_PACKAGE,
            [['id', 'in', published_package_ids]],
            ['sg_status_list', 'sg_task']
        )

    # for each entity, match task to tech_check_task only change status of the
    # matched ones.

    # make batch update
    updates = []
    target_status = sg_entity['sg_status_list']
    upstream_candidates = upstream_candidates_vs + published_files + \
                          published_packages
    for upstream_candidate in upstream_candidates:
        if upstream_candidate['sg_task'] == tech_check_task and \
                upstream_candidate['sg_status_list'] != target_status:
            # NOTE: assuming production server:
            upstream_url = sg.base_url + '/detail/%s/%d' % \
                           (upstream_candidate['type'],
                            upstream_candidate['id'])
            log.info('  update %s status to %s', upstream_url, target_status)
            updates.append({
                'request_type': 'update',
                'entity_type': upstream_candidate['type'],
                'entity_id': upstream_candidate['id'],
                'data': {'sg_status_list': target_status},
            })

    return updates


def handle_version_status_change(sg, log, event, _args):
    """Handle a version status change."""

    # skip if creating
    if event['meta'].get('in_create'):
        return

    if event['entity']:
        sg_entity = event['entity']
    else:
        log.warning(" >>> Skipping processing of this event: {}".format(event))
        log.warning(" >>> UNABLE TO GET ENTITY INFORMATION FOR THE EVENT!")
        return

    log.info('checking for version cascade for entity: %r', sg_entity)

    # update
    updates = form_updates(sg, log, sg_entity)
    if updates:
        log.info('batching %d updates', len(updates))
        sg.batch(updates)
