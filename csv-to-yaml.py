#!/usr/bin/env python

import csv

import click
import yaml


@click.command()
@click.option('--name', type=click.STRING)
@click.option('--description', default='', type=click.STRING)
@click.argument('source', type=click.File('r', encoding='utf-8-sig'))
@click.argument('target', type=click.File('w', encoding='utf-8'))
def csv_to_yaml(name, description, source, target):
    reader = csv.reader(source, delimiter=';')
    title = next(reader)
    indices = {s: i
               for (i, s)
               in enumerate(title)
               if s in ['Name', 'Vorname', 'E-Mail']}
    records = map(lambda r: line_to_record(r, indices),
                  [r for r in reader])
    output = {
        'teams': [
            {
                'teamname': name,
                'description': description,
                'users': list(map(lambda r: {
                    'username': r['E-Mail'].split('@')[0],
                    'fullname': f"{r['Vorname']} {r['Name']}",
                    'email': r['E-Mail']
                }, records))
            }
        ]}
    target.write(yaml.dump(output, allow_unicode=True))


def line_to_record(line, indices):
    return {name: line[i] for (name, i) in indices.items()}


if __name__ == '__main__':
    csv_to_yaml()
