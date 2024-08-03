def run(stackargs):

    '''
    this is platform versioning example 
    for the starting out guide
    '''

    # instantiate authoring stack
    stack = newStack(stackargs)

    # important to classify this stack
    # as a platform stack/configuration
    stack.set_platform()

    billing_tag = "eval-config0-2024"

    general_labels = {
        "environment": "dev",
        "purpose": "eval-config0"
    }

    # cloud_tags arguments are passed
    # as b64 string as cloud_tags_hash
    cloud_tags = {
        "name":"cloud_tags",
        "values": {
            "cloud_tags_hash": stack.b64_encode({
                **general_labels,
                "billing":billing_tag
            })
        }
    }

    # labels for resources that are added
    general = {
        "name":"general",
        "values":general_labels
    }

    do_cloud = {
        "name":"do_cloud",
        "values":{
            "provider":"digitalocean",
            "cloudprovider": "digitalocean"
        }
    }


    # digital ocean
    stack.add_substack("config0-publish:::jenkins_on_do",
                       arguments=[cloud_tags],
                       labels=[
                           general,
                           do_cloud
                       ])

    stack.add_substack("config0-publish:::doks",
                       arguments=[cloud_tags],
                       labels=[
                           general,
                           do_cloud
                       ])

    # drift detection of resources
    stack.add_substack('config0-publish:::check_drift_resources',
                       arguments=[cloud_tags],
                       labels=[general])

    stack.init_substacks()

    return stack.get_results()
