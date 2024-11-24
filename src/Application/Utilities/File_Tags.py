import plistlib

import xattr


def set_finder_tags(path, tags):
    try:
        # Encode the tags as a binary plist
        plist_data = plistlib.dumps(tags)

        # Set the extended attribute for Finder tags
        xattr.setxattr(path, 'com.apple.metadata:_kMDItemUserTags', plist_data)

    except Exception as e:
        print(f"Failed to set tags for {path}. Error: {e}")


def get_finder_tags(path):
    try:
        # Get the extended attribute for Finder tags
        attrs = xattr.getxattr(path, 'com.apple.metadata:_kMDItemUserTags')

        # Decode the binary plist to Python objects
        tags = plistlib.loads(attrs)
    except (KeyError, Exception):
        tags = ['No tags']

    return tags


def test_tag(file):
    tags = get_finder_tags(file)
    print(tags)

    set_finder_tags(file, [])
    tags = get_finder_tags(file)
    print(tags)

    set_finder_tags(file, ['Important'])
    tags = get_finder_tags(file)
    print(tags)


if __name__ == '__main__':
    file = '/Users/hans/Downloads/Code/Code.Rproj'
    test_tag(file)

    file = '/Users/hans/Downloads/Code'
    test_tag(file)

    file = '/Users/hans/Downloads/Code/New Probes - Single Tau/Overview all experiments - New Probes - Single Tau.Rmd'
    test_tag(file)
