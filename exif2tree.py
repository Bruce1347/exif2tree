#! /usr/bin/env python3
import datetime
from os import makedirs, rename
from os.path import exists, join, normpath
from pathlib import Path, PurePath

import click
import exifread


def insert_picture_in_dict(d, picture_tags, path):
    dt = datetime.datetime.strptime(
        picture_tags['Image DateTime'].values,
        '%Y:%m:%d %H:%M:%S',
    )
    year = dt.year
    month = dt.strftime('%m')
    day = dt.strftime('%d')

    if year not in d:
        d[year] = {}

    if month not in d[year]:
        d[year][month] = {}

    if day not in d[year][month]:
        d[year][month][day] = []

    d[year][month][day].append(
        dict(path=path, timestamp=dt),
    )


def create_tree(path):
    tree = {}
    fps = [path.open('rb') for path in Path(normpath(path)).rglob('*.CR2')]
    for fp in fps:
        tags = exifread.process_file(fp, details=False)
        insert_picture_in_dict(tree, tags, str(fp.name))

    for fp in fps:
        fp.close()
        assert fp.closed

    return tree


def build_rename_tree(tree):
    rename = []
    for year in tree:
        for month in tree[year]:
            for day in tree[year][month]:
                for f in tree[year][month][day]:
                    new_name = f['timestamp'].strftime('%H_%M_%S.CR2')
                    rename.append(
                        (f['path'], join(str(year), month, day, new_name))
                    )
    return rename


def rename_tree(tree, base_path, dry_run=False):
    rename_tree = build_rename_tree(tree)
    for path, new_name in rename_tree:
        new_path = join(base_path, new_name)
        if dry_run:
            print(f"DRY RUN: Moving {path} to {new_path}")
        else:
            print(f"Moving {path} to {new_path}")
            if not exists(PurePath(new_path).parent):
                makedirs(PurePath(new_path).parent)
            rename(path, new_path)


@click.command()
@click.argument('path', default='.')
@click.option('--rename', default=False, help='Automatically rename files')
@click.option('--dry', default=False, help='Make a dry run')
def main(path, rename, dry):
    tree = create_tree(path)
    if rename:
        rename_tree(tree, path, dry_run=dry)


if __name__ == '__main__':
    main()
