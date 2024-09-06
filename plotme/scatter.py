#!/usr/bin/env python

import argparse
import csv
import logging
import math
import random
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pylab import rcParams

import scipy.stats

import plotme.settings

COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
MARKERS = ('^', 'x', 'v', 'o', '<', '>', '1', '2', '3', '4', '8', 's', 'p', 'P', '*', 'h', 'H', '+', 'X', 'D', 'd', '.', ',', '|', '_')
CMAP_DEFAULT= (0.6, 0.6, 0.6, 0.5)  # non-numeric => black

def plot_scatter(data_fh, target, xlabel, ylabel, zlabel, figsize=12, fontsize=18, log=False, title=None, x_label=None, y_label=None, wiggle=0, delimiter='\t', z_color=None, z_color_map=None, label=None, join=False, y_annot=None, x_annot=None, dpi=72, markersize=20, z_cmap=None, x_squiggem=0.005, y_squiggem=0.005, marker='o', lines=[], line_of_best_fit=False):
  logging.info('starting...')
  try:
    matplotlib.style.use('seaborn-v0_8')
  except:
    matplotlib.style.use('seaborn')

  included = total = 0
  xvals = []
  yvals = []
  zvals = []
  cvals = []
  mvals = []
  lvals = []

  zvals_seen = []
  markers_seen = set()
  colors_seen = set()
  zvals_range = (1e99, -1e99)

  for row in csv.DictReader(data_fh, delimiter=delimiter):
    try:
      included += 1
      xval = float(row[xlabel]) + (random.random() - 0.5) * 2 * wiggle # x axis value
      yval = float(row[ylabel]) + (random.random() - 0.5) * 2 * wiggle # y axis value
      xvals.append(xval)
      yvals.append(yval)
      # process z
      if zlabel is not None:
        if row[zlabel] not in zvals_seen and z_cmap is None:
          zvals_seen.append(row[zlabel])

        z_color_map_found = False
        if z_color_map is not None: # directly map z values to a colour
          for m in z_color_map:
            logging.debug('splitting %s', m)
            name, value = m.rsplit(':', 1)
            logging.debug('comparing %s to %s', name, row[zlabel])
            if name == row[zlabel]:
              color, marker = value.split('/')
              cvals.append(color)
              colors_seen.add(color)
              mvals.append(marker)
              markers_seen.add(marker)
              z_color_map_found = True
              logging.debug('marker for %s added', name)
              break

        if z_color and not z_color_map_found and z_cmap is None: # use a predefined list of distinct colours
          ix = zvals_seen.index(row[zlabel])
          cvals.append(COLORS[ix % len(COLORS)])
          colors_seen.add(COLORS[ix % len(COLORS)])
          jx = int(ix / len(COLORS))
          mvals.append(MARKERS[jx % len(MARKERS)])
          markers_seen.add(MARKERS[jx % len(MARKERS)])

        if z_cmap is not None:
          try:
            zvals_range = (min((float(row[zlabel]), zvals_range[0])), max((float(row[zlabel]), zvals_range[1])))
          except ValueError:
            pass # skip non-numeric

        zvals.append(row[zlabel])

      if label is not None:
        lvals.append(row[label].replace('/', '\n'))

    except:
      logging.warning('Failed to include (is %s numeric?) %s', zlabel, row)
      raise

    total += 1

  # assign continuous color if z_cmap
  if z_cmap is not None:
    logging.info('cmap has range %s', zvals_range)
    cmap = matplotlib.cm.get_cmap(z_cmap)
    norm = matplotlib.colors.Normalize(vmin=zvals_range[0], vmax=zvals_range[1])
    m = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    cvals = []
    for x in zvals:
      try:
        cvals.append(m.to_rgba(float(x)))
      except ValueError:
        cvals.append(CMAP_DEFAULT)
    logging.debug(cvals)

  logging.info('finished reading %i of %i records', included, total)

  if len(xvals) == 0:
    logging.warning('No data to plot')
    return

  matplotlib.rcParams.update({'font.size': fontsize})
  fig = plt.figure(figsize=(figsize, 1 + int(figsize * len(yvals) / len(xvals))))
  ax = fig.add_subplot(111)

  if y_label is None:
    ax.set_ylabel(ylabel)
  else:
    logging.debug('y_label is %s', y_label)
    ax.set_ylabel(y_label)

  if x_label is None:
    ax.set_xlabel(xlabel)
  else:
    logging.debug('x_label is %s', x_label)
    ax.set_xlabel(x_label)

  if z_color or z_color_map is not None:
    for zval in zvals_seen:
      vals = [list(x) for x in zip(xvals, yvals, zvals, cvals, mvals) if x[2] == zval]
      marker = vals[0][4]
      if join:
        ax.plot([x[0] for x in vals], [x[1] for x in vals], c=vals[0][3], markersize=markersize, marker=marker, label=zval, alpha=0.8)
      else:
        ax.scatter([x[0] for x in vals], [x[1] for x in vals], c=[x[3] for x in vals], s=markersize, marker=marker, label=zval, alpha=0.8)
      ax.legend()
      #if join: # TODO does this work?
      #  ax.join([x[0] for x in vals], [x[1] for x in vals], c=[x[3] for x in vals], marker=vals[0][4], label=zval, alpha=0.8)
  elif z_cmap is not None:
    #logging.info('plotting %s %s %s %s %s', xvals, yvals, cvals, markersize, marker)
    ax.scatter(xvals, yvals, c=cvals, s=markersize, marker=marker)
    #cbar = ax.figure.colorbar(im, ax=ax, fraction=0.04, pad=0.01, shrink=0.5)
    ax.figure.colorbar(m, ax=ax, label=zlabel, fraction=0.04, pad=0.01, shrink=0.5)
  else:
    ax.scatter(xvals, yvals, s=markersize, marker=marker)
    if join:
      ax.plot(xvals, yvals)

  if line_of_best_fit:
    res = scipy.stats.linregress(xvals, yvals)
    logging.debug('xvals: %s res: %s', xvals, res)
    yvals_res = [res.intercept + res.slope * xval for xval in xvals]
    correlation = scipy.stats.pearsonr(xvals, yvals)
    ax.plot(xvals, yvals_res, color='orange', label='correlation {:.3f}\npvalue {:.3f}'.format(correlation[0], correlation[1]), linewidth=1)
    ax.legend()

  if zlabel is not None:
    if not z_color and not z_cmap:
      for x, y, z in zip(xvals, yvals, zvals):
        ax.annotate(z, (x, y), fontsize=fontsize)

  # alternative labelling
  if label is not None:
    for x, y, z in zip(xvals, yvals, lvals):
      ax.annotate(z, (x, y), fontsize=fontsize)

  if y_annot is not None:
    for ya in y_annot:
      color = 'red'
      if ':' in ya:
        ya, color = ya.split(':')
      label, height = ya.split('=')
      logging.debug('labelling line at %s with %s', height, label)
      ax.axhline(float(height), color=color, linewidth=1)
      ax.annotate(label, (min(xvals), float(height) + y_squiggem), fontsize=8)

  if x_annot is not None:
    color = 'red'
    for xa in x_annot:
      if ':' in xa:
        xa, color = xa.split(':')
      label, width = xa.split('=')
      logging.debug('labelling line at %s with %s', width, label)
      ax.axvline(float(width), color='red', linewidth=1)
      ax.annotate(label, (float(width) + x_squiggem, min(yvals)), fontsize=8)

  if lines is not None:
    for line in lines:
      x1, y1, x2, y2, c = line.split(',')
      ax.plot([float(x1), float(x2)], [float(y1), float(y2)], color=c, marker='')

  if title is not None:
    ax.set_title(title)

  if log: # does this work?
    ax.set_yscale('log')
    ax.set_xscale('log')

  logging.info('done processing %i of %i. saving to %s...', included, total, target)
  plt.tight_layout()
  plt.savefig(target, dpi=dpi, transparent=False) #plotme.settings.TRANSPARENT)
  matplotlib.pyplot.close('all')
  logging.info('done')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Scatter plot')
  parser.add_argument('--x', required=True, help='x column name')
  parser.add_argument('--y', required=True, help='y column name')
  parser.add_argument('--z', required=False, help='z column name (colour)')
  parser.add_argument('--label', required=False, help='label column')
  parser.add_argument('--z_color', action='store_true', help='use colours for z')
  parser.add_argument('--z_color_map', required=False, nargs='+', help='specify color/marker for z: label:color/marker')
  parser.add_argument('--z_cmap', required=False, help='z is continuous and use a color map')
  parser.add_argument('--title', required=False, help='z column name')
  parser.add_argument('--x_label', required=False, help='label on x axis')
  parser.add_argument('--y_label', required=False, help='label on y axis')
  parser.add_argument('--figsize', required=False, default=12, type=float, help='figsize width')
  parser.add_argument('--fontsize', required=False, default=18, type=int, help='fontsize')
  parser.add_argument('--markersize', required=False, default=20, type=int, help='fontsize')
  parser.add_argument('--marker', required=False, default='o', help='default marker')
  parser.add_argument('--dpi', required=False, default=plotme.settings.DPI, type=int, help='dpi')
  parser.add_argument('--wiggle', required=False, default=0, type=float, help='randomly perturb data')
  parser.add_argument('--x_squiggem', required=False, default=0.005, type=float, help='offset for text')
  parser.add_argument('--y_squiggem', required=False, default=0.005, type=float, help='offset for text')
  parser.add_argument('--delimiter', required=False, default='\t', help='input file delimiter')
  parser.add_argument('--log', action='store_true', help='log xy')
  parser.add_argument('--join', action='store_true', help='join points')
  parser.add_argument('--y_annot', required=False, nargs='*', help='add horizontal lines of the form label=height')
  parser.add_argument('--x_annot', required=False, nargs='*', help='add vertical lines of the form label=height')
  parser.add_argument('--lines', required=False, nargs='*', help='add unannotated lines of the form x1,y1,x2,y2,color')
  parser.add_argument('--line_of_best_fit', action='store_true', help='include line of best fit')
  parser.add_argument('--verbose', action='store_true', help='more logging')
  parser.add_argument('--target', required=False, default='plot.png', help='plot filename')
  args = parser.parse_args()
  if args.verbose:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
  else:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

  plot_scatter(sys.stdin, args.target, args.x, args.y, args.z, args.figsize, args.fontsize, args.log, args.title, args.x_label, args.y_label, args.wiggle, args.delimiter, args.z_color, args.z_color_map, args.label, args.join, args.y_annot, args.x_annot, args.dpi, args.markersize, args.z_cmap, args.x_squiggem, args.y_squiggem, args.marker, args.lines, args.line_of_best_fit)
