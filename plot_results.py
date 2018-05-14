import itertools
import json
import math
import os
from statistics import mean
from typing import Dict, List, Tuple, NamedTuple
from collections import namedtuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
from scipy import stats

# n_runs = 25
CONFIDENCE = 0.95
Z_STAR = 1.96
SAMPLE_FACTOR = 5

Stats = NamedTuple('Stats', [('mean', float),
                             ('std', float),
                             ('conf_lower', float),
                             ('conf_upper', float)])

ExperimentTimes = NamedTuple('ExperimentTimes',
                             [('processing', Stats),
                              ('uplink', Stats),
                              ('downlink', Stats)])


def autolabel(ax: plt.Axes, rects: List[plt.Rectangle], center=False) -> None:
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        x_pos = rect.get_x() + rect.get_width() / 2.0

        if center:
            y_pos = 0.5 * height + rect.get_y() if height >= 5.0 else \
                rect.get_y()
        else:
            y_pos = 1.01 * height + rect.get_y()
        ax.text(x_pos, y_pos,
                '{:02.2f}'.format(height),
                ha='center', va='bottom', weight='bold')


def plot_time_dist(experiments: Dict) -> None:
    root_dir = os.getcwd()
    up_results = []
    down_results = []
    proc_results = []
    for exp_name, exp_dir in experiments.items():
        os.chdir(root_dir + '/' + exp_dir)
        data = pd.read_csv('total_frame_stats.csv')
        processing = []
        uplink = []
        downlink = []
        for row in data.itertuples():
            proc = row.server_send - row.server_recv
            up = row.server_recv - row.client_send
            down = row.client_recv - row.server_send
            # rtt = row.client_recv - row.client_send
            if proc > 0:
                processing.append(proc)

            if up > 0:
                uplink.append(up)

            if down > 0:
                downlink.append(down)

        os.chdir('..')
        proc_results.append(processing)
        up_results.append(uplink)
        down_results.append(downlink)

    with plt.style.context('ggplot'):

        # processing times

        fig, ax = plt.subplots()
        abs_max = max([max(x) for x in proc_results])
        abs_min = min([min(x) for x in proc_results])
        if abs_min == 0:
            abs_min = 1

        bins = np.logspace(np.log10(abs_min), np.log10(abs_max), 30)

        for i, result in enumerate(proc_results):
            ax.hist(result, bins,
                    label=list(experiments.keys())[i],
                    # norm_hist=True
                    alpha=0.5,
                    density=True)

            shape, loc, scale = stats.lognorm.fit(result)
            pdf = stats.lognorm.pdf(bins, shape, loc, scale)
            ax.plot(bins, pdf,
                    label=list(experiments.keys())[i] + ' PDF')

        plt.title('Processing times')
        ax.set_xscale("log")
        ax.set_xlabel('Time [ms]')
        ax.set_ylabel('Density')
        plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        plt.show()

        # uplink times
        fig, ax = plt.subplots()
        abs_max = max([max(x) for x in up_results])
        abs_min = min([min(x) for x in up_results])
        if abs_min == 0:
            abs_min = 1

        bins = np.logspace(np.log10(abs_min), np.log10(abs_max), 30)
        # bins = np.linspace(abs_min, abs_max, 30)

        for i, result in enumerate(up_results):
            ax.hist(result, bins,
                    label=list(experiments.keys())[i],
                    # norm_hist=True
                    alpha=0.5,
                    density=True)

            # shape, loc, scale = lognorm.fit(result)
            # pdf = lognorm.pdf(bins, shape, loc, scale)
            # ax[1].plot(bins, pdf,
            #            label=list(experiments.keys())[i] + ' PDF')

        plt.title('Uplink times')
        ax.set_xscale("log")
        ax.set_xlabel('Time [ms]')
        ax.set_ylabel('Density')
        plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        plt.show()

        # downlink times
        fig, ax = plt.subplots()
        abs_max = max([max(x) for x in down_results])
        abs_min = min([min(x) for x in down_results])
        if abs_min == 0:
            abs_min = 1

        bins = np.logspace(np.log10(abs_min), np.log10(abs_max), 30)
        # bins = np.linspace(abs_min, abs_max, 30)

        for i, result in enumerate(down_results):
            ax.hist(result, bins,
                    label=list(experiments.keys())[i],
                    # norm_hist=True
                    alpha=0.5,
                    density=True)

            # shape, loc, scale = lognorm.fit(result)
            # pdf = lognorm.pdf(bins, shape, loc, scale)
            # ax[1].plot(bins, pdf,
            #            label=list(experiments.keys())[i] + ' PDF')

        plt.title('Downlink times')
        ax.set_xscale("log")
        ax.set_xlabel('Time [ms]')
        ax.set_ylabel('Density')

        plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        plt.show()


def plot_avg_times_frames(experiments: Dict, feedback: bool = False) -> None:
    root_dir = os.getcwd()

    stats = []

    for exp_dir in experiments.values():
        os.chdir(root_dir + '/' + exp_dir)
        data = pd.read_csv('total_frame_stats.csv', index_col=0)
        os.chdir(root_dir)

        stats.append(frames_stats(data, feedback=feedback))

    processing_means = [s.processing.mean for s in stats]
    processing_errors = [[s.processing.mean - s.processing.conf_lower
                          for s in stats],
                         [s.processing.conf_upper -
                          s.processing.mean
                          for s in stats]]

    uplink_means = [s.uplink.mean for s in stats]
    uplink_errors = [[s.uplink.mean - s.uplink.conf_lower
                      for s in stats],
                     [s.uplink.conf_upper -
                      s.uplink.mean
                      for s in stats]]

    downlink_means = [s.downlink.mean for s in stats]
    downlink_errors = [[s.downlink.mean - s.downlink.conf_lower
                        for s in stats],
                       [s.downlink.conf_upper -
                        s.downlink.mean
                        for s in stats]]

    bar_width = 0.3
    r1 = np.arange(len(experiments))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]

    errorbar_opts = dict(
        ecolor='darkorange',
        lw=2, alpha=1.0,
        capsize=0, capthick=1
    )

    fig, ax = plt.subplots()
    rect1 = ax.bar(r1, uplink_means,
                   label='Avg. uplink time',
                   yerr=uplink_errors,
                   width=bar_width,
                   edgecolor='white',
                   error_kw=dict(errorbar_opts, label='95% Confidence Int.')
                   )
    rect2 = ax.bar(r2, processing_means,
                   label='Avg. processing time',
                   yerr=processing_errors,
                   width=bar_width,
                   edgecolor='white',
                   error_kw=errorbar_opts
                   )
    rect3 = ax.bar(r3, downlink_means,
                   label='Avg. downlink time',
                   yerr=downlink_errors,
                   width=bar_width,
                   edgecolor='white',
                   error_kw=errorbar_opts
                   )

    autolabel(ax, rect1)
    autolabel(ax, rect2)
    autolabel(ax, rect3)

    ax.set_ylabel('Time [ms]')
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")

    # Add xticks on the middle of the group bars
    if feedback:
        plt.title('Time statistics for frames w/ feedback')
    else:
        plt.title('Time statistics for frames w/o feedback')
    plt.xlabel('Number of clients', fontweight='bold')
    plt.xticks([r + bar_width for r in range(len(experiments))],
               experiments.keys())

    plt.tight_layout()
    plt.show()


def frames_stats(data: pd.DataFrame, feedback: bool = False) -> ExperimentTimes:
    if feedback:
        frame_data = data.loc[data['feedback']]
    else:
        # filter only frames without feedback
        frame_data = data.loc[~data['feedback']]

    frame_data['processing'] = \
        frame_data['server_send'] - frame_data['server_recv']
    frame_data['uplink'] = \
        frame_data['server_recv'] - frame_data['client_send']
    frame_data['downlink'] = \
        frame_data['client_recv'] - frame_data['server_send']

    # only count frames with positive values (time can't be negative)
    frame_data = frame_data.loc[frame_data['processing'] > 0]
    frame_data = frame_data.loc[frame_data['uplink'] > 0]
    frame_data = frame_data.loc[frame_data['downlink'] > 0]

    # if not feedback:
    #     # finally, only consider every 3rd frame for non-feedback frames
    #     frame_data = frame_data.iloc[::3, :]

    n_runs = frame_data['run_id'].max() + 1

    if feedback:
        samples = [frame_data.loc[frame_data['run_id'] == run_id].sample()
                   for run_id in range(n_runs)]
    else:
        # find number of clients
        n_clients = frame_data['client_id'].max() + 1
        # take SAMPLE_FACTOR samples per client per run
        samples = []
        for run_id in range(n_runs):
            run_data = frame_data.loc[frame_data['run_id'] == run_id]
            for client_id in range(n_clients):
                client_data = run_data.loc[run_data['client_id'] == client_id]
                samples.append(client_data.sample(n=SAMPLE_FACTOR))

    samples = pd.concat(samples)

    # stats for processing times:
    proc_mean = samples['processing'].mean()
    proc_std = samples['processing'].std()
    proc_conf = stats.norm.interval(CONFIDENCE,
                                    loc=proc_mean,
                                    scale=proc_std / math.sqrt(n_runs))
    proc_stats = Stats(proc_mean, proc_std, *proc_conf)

    # stats for uplink times:
    up_mean = samples['uplink'].mean()
    up_std = samples['uplink'].std()
    up_conf = stats.norm.interval(CONFIDENCE,
                                  loc=up_mean,
                                  scale=up_std / math.sqrt(n_runs))
    up_stats = Stats(up_mean, up_std, *up_conf)

    # stats for downlink times:
    down_mean = samples['downlink'].mean()
    down_std = samples['downlink'].std()
    down_conf = stats.norm.interval(CONFIDENCE,
                                    loc=down_mean,
                                    scale=down_std / math.sqrt(n_runs))
    down_stats = Stats(down_mean, down_std, *down_conf)

    return ExperimentTimes(proc_stats, up_stats, down_stats)


def plot_cpu_loads(experiments: Dict) -> None:
    system_data = [load_system_data_for_experiment(x)
                   for x in experiments.values()]
    cpu_loads = [x['cpu_load'].mean() for x in system_data]

    fig, ax = plt.subplots()
    rect = ax.bar(experiments.keys(), cpu_loads, label='Average CPU load')
    autolabel(ax, rect)

    ax.set_ylabel('Load [%]')
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.show()


def plot_ram_usage(experiments: Dict) -> None:
    system_data = [load_system_data_for_experiment(x)
                   for x in experiments.values()]

    total_mem = psutil.virtual_memory().total
    ram_usage = [(total_mem - x['mem_avail']).mean() for x in system_data]
    ram_usage = [x / float(1024 * 1024 * 1024) for x in ram_usage]

    fig, ax = plt.subplots()
    rect = ax.bar(experiments.keys(), ram_usage, label='Average RAM usage')
    autolabel(ax, rect)

    # ax.set_ylim([0, total_mem + 3])
    ax.axhline(y=total_mem / float(1024 * 1024 * 1024),
               color='red',
               label='Max. available memory')
    ax.set_ylabel('Usage [GiB]')
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.show()


def load_data_for_experiment(experiment_id) -> Dict:
    os.chdir(experiment_id)
    with open('total_stats.json', 'r') as f:
        os.chdir('..')
        return json.load(f)


def load_system_data_for_experiment(experiment_id) -> pd.DataFrame:
    os.chdir(experiment_id)
    df = pd.read_csv('total_system_stats.csv')
    os.chdir('..')
    return df


if __name__ == '__main__':
    with plt.style.context('ggplot'):
        experiments = {
            '1 Client'  : '1Client_Benchmark',
            '5 Clients' : '5Clients_Benchmark',
            '10 Clients': '10Clients_Benchmark'
        }

        plot_avg_times_frames(experiments, feedback=True)
        plot_avg_times_frames(experiments, feedback=False)

    # plot_avg_times_runsample(experiments)
    # # plot_avg_times_framesample(experiments)
    # plot_cpu_loads(experiments)
    # plot_ram_usage(experiments)
    # plot_time_dist(experiments)
