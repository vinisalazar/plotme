#!/usr/bin/env python

import argparse
import csv
import logging
import math
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pylab import rcParams

def plot_heat(data_fh, target, xlabel, ylabel, zlabel, figsize, log, title, cmap, text_switch, x_label, y_label):
  logging.info('starting...')

  # Sample  Tags    Caller  DP      AF      Error   Variants        Multiplier      Signature.1     ...    Signature.30
  included = total = 0
  results = {}
  xvals = set()
  yvals = set()
  max_zval = 0.0
  for row in csv.DictReader(data_fh, delimiter='\t'):
    try:
      included += 1
      xval = float(row[xlabel]) # x axis value
      yval = float(row[ylabel]) # y axis value
      xvals.add(xval)
      yvals.add(yval)
      if log:
        zval = math.log(float(row[zlabel]) + 1.0)
      else:
        zval = float(row[zlabel])
      results['{},{}'.format(xval, yval)] = zval
      max_zval = max(max_zval, zval)
    except:
      logging.debug('Failed to include %s', row)

    total += 1

  logging.info('finished reading %i of %i records with max_zval %.2f', included, total, max_zval)

  if len(results) == 0:
    logging.warn('No data to plot')
    return

  xvals = sorted(list(xvals))
  yvals = sorted(list(yvals))[::-1] # bottom left

  zvals = []
  tvals = []

  for y in yvals:
    zrow = []
    trow = []
    for x in xvals:
      key = '{},{}'.format(x, y)
      if key in results:
        zrow.append(results[key])
        trow.append('{:.2f}'.format(results[key]))
      else:
        zrow.append(0.0)
        trow.append('')
    zvals.append(zrow)
    tvals.append(trow)

  fig = plt.figure(figsize=(figsize, 1 + int(figsize * len(yvals) / len(xvals))))
  ax = fig.add_subplot(111)
  if cmap is None:
    im = ax.imshow(zvals)
  else:
    im = ax.imshow(zvals, cmap=cmap)

  cbar = ax.figure.colorbar(im, ax=ax, fraction=0.04, pad=0.01, shrink=0.9)
  cbar.ax.set_ylabel(zlabel, rotation=-90, va="bottom")

  ax.set_xticks(range(len(xvals)))
  ax.set_yticks(range(len(yvals)))
  ax.set_xticklabels(xvals)
  ax.set_yticklabels(yvals)

  if y_label is None:
    ax.set_ylabel(ylabel)
  else:
    ax.set_ylabel(y_label)

  if x_label is None:
    ax.set_xlabel(xlabel)
  else:
    ax.set_xlabel(x_label)

  for y in range(len(yvals)):
    for x in range(len(xvals)):
      if zvals[y][x] > max_zval * text_switch:
        text = ax.text(x, y, tvals[y][x], ha="center", va="center", color="k")
      else:
        text = ax.text(x, y, tvals[y][x], ha="center", va="center", color="w")

  if title is None:
    ax.set_title('{} given {} and {}'.format(zlabel, xlabel, ylabel))
  else:
    ax.set_title(title)

  logging.info('done processing %i of %i', included, total)
  plt.tight_layout()
  plt.savefig(target)
  matplotlib.pyplot.close('all')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Plot changes in signature')
  parser.add_argument('--x', required=True, help='x column name')
  parser.add_argument('--y', required=True, help='y column name')
  parser.add_argument('--z', required=True, help='z column name')
  parser.add_argument('--title', required=False, help='z column name')
  parser.add_argument('--x_label', required=False, help='label on x axis')
  parser.add_argument('--y_label', required=False, help='label on y axis')
  parser.add_argument('--cmap', required=False, help='cmap name')
  parser.add_argument('--figsize', required=False, default=12, type=int, help='figsize width')
  parser.add_argument('--text_switch', required=False, default=0.5, type=float, help='where to change text colour')
  parser.add_argument('--log', action='store_true', help='log z')
  parser.add_argument('--verbose', action='store_true', help='more logging')
  parser.add_argument('--target', required=False, default='plot.png', help='plot filename')
  args = parser.parse_args()
  if args.verbose:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
  else:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

  plot_heat(sys.stdin, args.target, args.x, args.y, args.z, args.figsize, args.log, args.title, args.cmap, args.text_switch, args.x_label, args.y_label)
