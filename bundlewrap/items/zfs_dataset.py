from pipes import quote

from bundlewrap.exceptions import BundleError
from bundlewrap.items import Item
from bundlewrap.utils.text import mark_for_translation as _


class ZFSDataset(Item):
    """
    Creates ZFS datasets and manages their options.
    """
    BUNDLE_ATTRIBUTE_NAME = "zfs_datasets"
    REJECT_UNKNOWN_ATTRIBUTES = False
    ITEM_TYPE_NAME = "zfs_dataset"
    PROPERTY_DEFAULTS = {
        'mountpoint': 'none',
        'mounted': 'no',
    }

    def __repr__(self):
        return f"<ZFSDataset name:{self.name} {' '.join(f'{k}:{v}' for k,v in self.__item_properties().items())}>"

    # PROPERTIES
    
    def __item_properties(self):
        # remove properties with value of None
        return {
            property: value
                for property, value in self.attributes.items()
                if value
        }

    def __changed_properties(self):
        if self.__does_exist():
            cmd = f'zfs get all {self.name} -p -H -o property,value -s local'
            return dict(
                line.split('\t')
                    for line in self.run(cmd).stdout.decode('utf-8').strip().splitlines()
            )
        else:
            return {}
    
    def __properties_now(self):
        # affected properties in their current state:
        # - changed properties have their value set
        # - the remaining item properties have their default set
        return {
            **{
                name: self.PROPERTY_DEFAULTS.get(name)
                    for name in self.__item_properties()
            },
            **self.__changed_properties(),
        }

    def __properties_after(self):
        # affected properties in their final state:
        # - item properties have their value set
        # - the remaining changed properties have their default set
        return {
            **{
                name: self.PROPERTY_DEFAULTS.get(name)
                    for name in self.__changed_properties()
            },
            **self.__item_properties(),
        }
    
    # HELPERS

    def __create(self):
        properties_string = ' '.join(
            f'-o {property}={quote(value)}'
                for property, value in self.__item_properties().items()
        )
        self.run(f'zfs create {properties_string} {self.name}')

    def __does_exist(self):
        return self.run(f'zfs list {self.name}', may_fail=True).return_code == 0

    def __set_property(self, option, value):
        if value == None:
            self.run(f'zfs inherit -S {quote(option)} {quote(self.name)}')
        else:
            self.run(f'zfs set {quote(option)}={quote(value)} {quote(self.name)}')
    
    # ITEM

    def sdict(self):
        if self.__does_exist():
            return {
                **self.__properties_now(),
                'mounted': self.run(f'zfs get mounted {self.name} -p -H -o value').stdout.decode('utf-8').strip(),
            }
        else:
            return None

    def fix(self, status):
        if status.must_be_created:
            self.__create()
        else:
            for property in status.keys_to_fix:
                if property == 'mounted':
                    if status.cdict[property] == 'yes':
                        self.run(f'zfs mount {quote(self.name)}')
                    else:
                        self.run(f'zfs umount {quote(self.name)}')
                else:
                    self.__set_property(property, status.cdict[property])

    def cdict(self):
        return {
            **self.__properties_after(),
            'mounted': 'yes' if self.__properties_after().get('mountpoint') else 'no',
        }

    # DEPENDENCIES

    def get_auto_attrs(self, items):
        pool = self.name.split("/")[0]
        pool_item_found = False
        parent_dataset = '/'.join(self.name.split('/')[0:-1])
        needs = set()

        for item in items:
            if item.ITEM_TYPE_NAME == "zfs_pool" and item.name == pool:
                # add dependency to the pool this dataset resides on
                pool_item_found = True
                needs.add(f'zfs_pool:{pool}')
            elif (
                item.ITEM_TYPE_NAME == "zfs_dataset" and
                item.name == parent_dataset
            ):
                # add dependency to parent dataset
                needs.add(item.id)
            elif self.__item_properties().get('mountpoint'):
                parent_directory = '/'.join(self.__item_properties().get('mountpoint', '').split('/')[0:-1])
                if (
                    item.ITEM_TYPE_NAME == "zfs_dataset" and
                    item.attributes.get('mountpoint') == parent_directory or
                    item.ITEM_TYPE_NAME == "directory" and
                    item.name == parent_directory
                ):
                    # add dependency to parent mountpoint or directory
                    needs.add(item.id)

        if not pool_item_found:
            raise BundleError(_(
                f'ZFS dataset {self.name} resides on pool {pool} but item '
                'zfs_pool:{dep} does not exist'
            ))
            
        return {'needs': needs}
