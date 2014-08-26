#!/usr/bin/python
import argparse
import sys, os
import sqlite3 as sq
import plantcv as pcv
from shutil import copy
import datetime
import re

### Parse command-line arguments
def options():
  parser = argparse.ArgumentParser(description="Extract VIS object shape data from an SQLite database")
  parser.add_argument("-d", "--database", help="SQLite database file from plantcv.")
  parser.add_argument("-c", "--csv", help="PhenoFront CSV file.")
  parser.add_argument("-f", "--file", help="File containing plant IDs.", required=True)
  parser.add_argument("-o", "--outdir", help="Output directory.", required=True)
  parser.add_argument("--vis", help="Images are class VIS.", action='store_true')
  parser.add_argument("--nir", help="Images are class NIR.", action='store_true')
  parser.add_argument("--flu", help="Images are class FLU.", action='store_true')
  args = parser.parse_args()
  return args

### Dictionary factory for SQLite query results
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

### Database image lookup method
def db_lookup(database, ids, outdir, vis=False, nir=False, flu=False):
  # Does the database exist?
  if not os.path.exists(database):
    pcv.fatal_error("The database file " + str(database) + " does not exist");
  
  # Open a connection
  try:
    connect=sq.connect(database)
  except sq.Error, e:
    print("Error %s:" % e.args[0])
  
  # Replace the row_factory result constructor with a dictionary constructor
  connect.row_factory = dict_factory
  # Change the text output format from unicode to UTF-8
  connect.text_factory=str

   # Database handler
  db = connect.cursor()
  
  for plant_id in ids:
    for row in (db.execute('SELECT * FROM `snapshots` WHERE `plant_id` = "%s"' % plant_id)):
      dt = datetime.datetime.fromtimestamp(row['datetime']).strftime('%Y-%m-%d_%H:%M:%S')
      if (vis):
        if (row['camera'] == 'vis_sv' or row['camera'] == 'vis_tv'):
          img_name = outdir + '/' + row['plant_id'] + '_' + row['camera'] + '_' + str(row['frame']) + '_z' + str(row['zoom']) + '_h' + str(row['lifter']) + '_' + dt + '.png'
          copy(row['image_path'], img_name)
          #print(args.outdir + '/' + row['plant_id'])
      if (nir):
        if (row['camera'] == 'nir_sv' or row['camera'] == 'nir_tv'):
          img_name = outdir + '/' + row['plant_id'] + '_' + row['camera'] + '_' + str(row['frame']) + '_z' + str(row['zoom']) + '_h' + str(row['lifter']) + '_' + dt + '.png'
          copy(row['image_path'], img_name)
      if (flu):
        if (row['camera'] == 'flu_tv'):
          images = row['image_path'].split(',')
          for i in enumerate(images):
            img_name = outdir + '/' + row['plant_id'] + '_' + row['camera'] + '_' + str(row['frame']) + '_z' + str(row['zoom']) + '_h' + str(row['lifter']) + '_' + str(i) + '_' + dt + '.png'
            copy(images[i], outdir)
  
### CSV image lookup method
def csv_lookup(csv, ids, outdir, vis=False, nir=False, flu=False):
  # Regexs
  vis_pattern = re.compile('^vis', re.IGNORECASE)
  nir_pattern = re.compile('^nir', re.IGNORECASE)
  flu_pattern = re.compile('^Flu', re.IGNORECASE)
  
  path, img = os.path.split(csv)
  
  # Open CSV file
  with open(csv) as snapshots:
    for row in snapshots:
      snapshot = row.rstrip('\n')
      data = snapshot.split(',')
      date = data[3].split(' ')
      if (data[1] in ids):
        tiles = data[9].split(';')
        for tile in tiles:
          img_name = outdir + '/' + data[1] + '_' + tile + '_' + date[0] + '_' + date[1] + '.png'
          if (vis):
            if (vis_pattern.match(tile)):
              copy(path + '/snapshot' + data[0] + '/' + tile + '.png', img_name)
          if (nir):
            if (nir_pattern.match(tile)):
              copy(path + '/snapshot' + data[0] + '/' + tile + '.png', img_name)
          if (flu):
            if (flu_pattern.match(tile)):
              copy(path + '/snapshot' + data[0] + '/' + tile + '.png', img_name)

### Create dictionary of plant_id from file
def dict_plant_id(infile):
  # Store plant IDs
  ids = {}
  
  # Open input file
  with open(infile) as plant_ids:
    for plant_id in plant_ids:
      pid = plant_id.rstrip('\n')
      ids[pid] = 1
  
  return ids

### Main pipeline
def main():
  # Get options
  args = options()
  
  plant_ids = dict_plant_id(args.file)
  
  if (args.database):
    db_lookup(args.database, plant_ids, args.outdir, args.vis, args.nir, args.flu)
  elif (args.csv):
    csv_lookup(args.csv, plant_ids, args.outdir, args.vis, args.nir, args.flu)
  

if __name__ == '__main__':
  main()