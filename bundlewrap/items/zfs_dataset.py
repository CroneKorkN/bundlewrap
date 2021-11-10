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

    def __repr__(self):
        return f"<ZFSDataset name:{self.name} {' '.join(f'{k}:{v}' for k,v in self.attributes.items())}>"

    def __all_attrs(self, source='local,default,inherited,temporary,received'):
        cmd = f'zfs get all {self.name} -p -H -o property,value -s {source}'
        return dict(
            line.split('\t')
                for line in self.run(cmd).stdout.decode('utf-8').strip().splitlines()
        )

    def __create(self, options):
        option_list = []
        for option, value in sorted(options.items()):
            # We must exclude the 'mounted' property here because it's a
            # read-only "informational" property.
            if option != 'mounted' and value is not None:
                option_list.append("-o {}={}".format(quote(option), quote(value)))
        option_args = " ".join(option_list)

        self.run(
            "zfs create {} {}".format(
                option_args,
                quote(self.name),
            ),
            may_fail=True,
        )

        if options['mounted'] == 'no':
            self.__set_option('mounted', 'no')

    def __does_exist(self):
        status_result = self.run(
            "zfs list {}".format(quote(self.name)),
            may_fail=True,
        )
        return status_result.return_code == 0

    def __get_option(self, option):
        cmd = "zfs get -Hp -o value {} {}".format(quote(option), quote(self.name))
        # We always expect this to succeed since we don't call this function
        # if we have already established that the dataset does not exist.
        status_result = self.run(cmd)
        return status_result.stdout.decode('utf-8').strip()

    def __set_option(self, option, value):
        if option == 'mounted':
            # 'mounted' is a read-only property that can not be altered by
            # 'set'. We need to call 'zfs mount tank/foo'.
            self.run(
                "zfs {} {}".format(
                    "mount" if value == 'yes' else "unmount",
                    quote(self.name),
                ),
                may_fail=True,
            )
        else:
            self.run(
                "zfs set {}={} {}".format(
                    quote(option),
                    quote(value),
                    quote(self.name),
                ),
                may_fail=True,
            )

    def cdict(self):
        print(self.__all_attrs())
        print(self.__all_attrs(source='local'))
        cdict = {}
        for option, value in self.attributes.items():
            if option == 'mountpoint' and value is None:
                value = "none"
            if value is not None:
                cdict[option] = value
        cdict['mounted'] = 'no' if cdict.get('mountpoint') in (None, "none") else 'yes'
        return cdict

    def fix(self, status):
        if status.must_be_created:
            self.__create(status.cdict)
        else:
            for option in status.keys_to_fix:
                self.__set_option(self.name, option, status.cdict[option])

    def get_auto_attrs(self, items):
        pool = self.name.split("/")[0]
        pool_item = "zfs_pool:{}".format(pool)
        pool_item_found = False
        needs = set()

        for item in items:
            if item.ITEM_TYPE_NAME == "zfs_pool" and item.name == pool:
                # Add dependency to the pool this dataset resides on.
                pool_item_found = True
                needs.add(pool_item)
            elif (
                item.ITEM_TYPE_NAME == "zfs_dataset" and
                self.name != item.name
            ):
                # Find all other datasets that are parents of this
                # dataset.
                # XXX Could be optimized by finding the "largest"
                # parent only.
                if self.name.startswith(item.name + "/"):
                    needs.add(item.id)
                elif (
                    self.attributes.get('mountpoint') and
                    item.attributes.get('mountpoint') and
                    self.attributes['mountpoint'].startswith(item.attributes['mountpoint'])
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

    def sdict(self):
        if not self.__does_exist():
            return None

        sdict = {}
        for option in self.attributes:
            sdict[option] = self.__get_option(option)
        sdict['mounted'] = self.__get_option('mounted')
        return sdict
