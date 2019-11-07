"""
TODO how to stats artists
"""
import argparse
import collections
import random
import timeit
from itertools import cycle
from multiprocessing import Manager
from multiprocessing.pool import Pool
from typing import List, Optional

import matplotlib.pyplot as plt
import tables

from lakh_utils import get_msd_score_matches
from lakh_utils import msd_id_to_h5
from threading_utils import Counter

parser = argparse.ArgumentParser()
parser.add_argument("--sample_size", type=int, default=1000)
parser.add_argument("--path_dataset_dir", type=str, required=True)
parser.add_argument("--path_match_scores_file", type=str, required=True)
args = parser.parse_args()

MSD_SCORE_MATCHES = get_msd_score_matches(args.path_match_scores_file)


def process(msd_id: str, counter: Counter) -> Optional[dict]:
  try:
    with tables.open_file(msd_id_to_h5(msd_id, args.path_dataset_dir)) as h5:
      counter.increment()
      artist = h5.root.metadata.songs.cols.artist_name[0].decode("utf-8")
      return {"msd_id": msd_id, "artist": artist}
  except Exception as e:
    print(f"Exception during processing of {msd_id}: {e}")
    return


def app(msd_ids: List[str]):
  start = timeit.default_timer()

  # TODO info
  with Pool(4) as pool:
    manager = Manager()
    counter = Counter(manager, len(msd_ids))
    print("START")
    results = pool.starmap(process, zip(msd_ids, cycle([counter])))
    results = [result for result in results if result]
    print("END")
    results_percentage = len(results) / len(msd_ids) * 100
    print(f"Number of tracks: {len(MSD_SCORE_MATCHES)}, "
          f"number of tracks in sample: {len(msd_ids)}, "
          f"number of results: {len(results)} "
          f"({results_percentage}%)")

  # TODO histogram
  artists = [result["artist"] for result in results]
  most_common_artists = collections.Counter(artists).most_common(20)
  print(f"Most common artists: {most_common_artists}")
  plt.bar([artist for artist, _ in most_common_artists],
          [count for _, count in most_common_artists])
  plt.title("Artist song count")
  plt.xticks(rotation=30, ha="right")
  plt.ylabel("count")
  plt.show()

  stop = timeit.default_timer()
  print("Time: ", stop - start)


if __name__ == "__main__":
  if args.sample_size:
    # Process a sample of it
    MSD_IDS = random.sample(list(MSD_SCORE_MATCHES), args.sample_size)
  else:
    # Process all the dataset
    MSD_IDS = list(MSD_SCORE_MATCHES)
  app(MSD_IDS)
