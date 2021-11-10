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
        return f"<ZFSDataset name:{self.name} {' '.join(f'{k}:{v}' for k,v in self.attributes.items())}>"

    # PROPERTIES

    def __changed_properties(self):
        if self.__does_exist():
            cmd = f'zfs get all {self.name} -p -H -o property,value -s local'
            return dict(
                line.split('\t')
                    for line in self.run(cmd).stdout.decode('utf-8').strip().splitlines()
            )
        else:
            return {}
    
    def __affected_properties_now(self):
        return {
            **{
                name: self.PROPERTY_DEFAULTS.get(name)
                    for name in self.attributes
            },
            **self.__changed_properties(),
        }

    def __affected_properties_after(self):
        return {
            **{
                name: self.PROPERTY_DEFAULTS.get(name)
                    for name in self.__changed_properties()
            },
            **self.attributes,
        }
    
    # HELPERS

    def __create(self):
        properties_string = ' '.join(
            f'-o {property}={quote(value)}'
                for property, value in self.__affected_properties_after().items()
                if value is not None
        )
        self.run(f'zfs create {properties_string} {self.name}')

    def __does_exist(self):
        return self.run(f'zfs list {self.name}', may_fail=True).return_code == 0

    def __set_property(self, option, value):
        if value == None:
            self.run(f'zfs inherit -S {quote(option)} {quote(self.name)}')
        else:
            self.run(f'zfs set {quote(option)}={quote(value)} {quote(self.name)}')
    
    # CORE

    # before
    def sdict(self):
        if self.__does_exist():
            return {
                **self.__affected_properties_now(),
                'mounted': self.run(f'zfs get mounted {self.name} -p -H -o value').stdout.decode('utf-8').strip(),
            }
        else:
            return None

    # perform
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

    # after
    def cdict(self):
        return {
            **self.__affected_properties_after(),
            'mounted': 'no' if self.__affected_properties_after().get('mountpoint') == None else 'yes',
        }

    # DEPENDENCIES

    def get_auto_attrs(self, items):
        pool = self.name.split("/")[0]
        pool_item = "zfs_pool:{}".format(pool)
        parent_dataset = '/'.join(self.name.split('/')[0:-1])
        pool_item_found = False
        needs = set()

        for item in items:
            if item.ITEM_TYPE_NAME == "zfs_pool" and item.name == pool:
                # Add dependency to the pool this dataset resides on.
                pool_item_found = True
                needs.add(pool_item)
            elif (
                item.ITEM_TYPE_NAME == "zfs_dataset" and
                item.name == '/'.join(self.name.split('/')[0:-1])
            ):
                needs.add(item.id)
            elif self.attributes.get('mountpoint'):
                parent_directory = '/'.join(self.attributes.get('mountpoint', '').split('/')[0:-1])
                if (
                    item.ITEM_TYPE_NAME == "zfs_dataset" and
                    item.attributes.get('mountpoint') == parent_directory or
                    item.ITEM_TYPE_NAME == "directory" and
                    item.name == parent_directory
                ):
                    needs.add(item.id)

        if not pool_item_found:
            raise BundleError(_(
                "ZFS dataset {dataset} resides on pool {pool} but item "
                "{dep} does not exist"
            ).format(
                dataset=self.name,
                pool=pool,
                dep=pool_item,
            ))
            
        return {'needs': needs}
