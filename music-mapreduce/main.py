#!/usr/bin/env python
#
# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" This is a sample application that tests the MapReduce API.

It does so by allowing users to upload a zip file containing plaintext files
and perform some kind of analysis upon it. Currently three types of MapReduce
jobs can be run over user-supplied input data: a WordCount MR that reports the
number of occurrences of each word, an Index MR that reports which file(s) each
word in the input corpus comes from, and a Phrase MR that finds statistically
improbably phrases for a given input file (this requires many input files in the
zip file to attain higher accuracies)."""

__author__ = """aizatsky@google.com (Mike Aizatsky), cbunch@google.com (Chris
Bunch)"""

# Using opensource naming conventions, pylint: disable=g-bad-name

import datetime
import jinja2
import logging
import re
import operator
import urllib
import webapp2

from google.appengine.ext import blobstore
from google.appengine.ext import db

from google.appengine.ext.webapp import blobstore_handlers

from google.appengine.api import app_identity
from google.appengine.api import taskqueue
from google.appengine.api import users

from mapreduce import base_handler
from mapreduce import mapreduce_pipeline
from mapreduce import operation as op
from mapreduce import shuffler


class FileMetadata(db.Model):
  """A helper class that will hold metadata for the user's blobs.

  Specifially, we want to keep track of who uploaded it, where they uploaded it
  from (right now they can only upload from their computer, but in the future
  urlfetch would be nice to add), and links to the results of their MR jobs. To
  enable our querying to scan over our input data, we store keys in the form
  'user/date/blob_key', where 'user' is the given user's e-mail address, 'date'
  is the date and time that they uploaded the item on, and 'blob_key'
  indicates the location in the Blobstore that the item can be found at. '/'
  is not the actual separator between these values - we use '..' since it is
  an illegal set of characters for an e-mail address to contain.
  """

  __SEP = ".."
  __NEXT = "./"

  owner = db.UserProperty()
  filename = db.StringProperty()
  uploadedOn = db.DateTimeProperty()
  source = db.StringProperty()
  blobkey = db.StringProperty()
  songsoldnum_link = db.StringProperty()
  dollarsong_link = db.StringProperty()
  songartist_link = db.StringProperty()
  dollarartist_link = db.StringProperty()
  jazzsongsoldnum_link = db.StringProperty()
  jazzdollarsong_link = db.StringProperty()
  jazzsongartist_link = db.StringProperty()
  jazzdollarartist_link = db.StringProperty()
  mostbuytogether_link = db.StringProperty()


  songsoldnum_link1 = db.StringProperty()
  songsoldnum_link2 = db.StringProperty()
  songsoldnum_link3 = db.StringProperty()
  dollarsong_link1 = db.StringProperty()
  dollarsong_link2 = db.StringProperty()
  dollarsong_link3 = db.StringProperty()
  songartist_link1 = db.StringProperty()
  songartist_link2 = db.StringProperty()
  songartist_link3 = db.StringProperty()
  dollarartist_link1 = db.StringProperty()
  dollarartist_link2 = db.StringProperty()
  dollarartist_link3 = db.StringProperty()
  jazzsongsoldnum_link1 = db.StringProperty()
  jazzsongsoldnum_link2 = db.StringProperty()
  jazzsongsoldnum_link3 = db.StringProperty()
  jazzdollarsong_link1 = db.StringProperty()
  jazzdollarsong_link2 = db.StringProperty()
  jazzdollarsong_link3 = db.StringProperty()
  jazzsongartist_link1 = db.StringProperty()
  jazzsongartist_link2 = db.StringProperty()
  jazzsongartist_link3 = db.StringProperty()
  jazzdollarartist_link1 = db.StringProperty()
  jazzdollarartist_link2 = db.StringProperty()
  jazzdollarartist_link3 = db.StringProperty()
  mostbuytogether_link1 = db.StringProperty()
  mostbuytogether_link2 = db.StringProperty()
  mostbuytogether_link3 = db.StringProperty()


  @staticmethod
  def getFirstKeyForUser(username):
    """Helper function that returns the first possible key a user could own.

    This is useful for table scanning, in conjunction with getLastKeyForUser.

    Args:
      username: The given user's e-mail address.
    Returns:
      The internal key representing the earliest possible key that a user could
      own (although the value of this key is not able to be used for actual
      user data).
    """

    return db.Key.from_path("FileMetadata", username + FileMetadata.__SEP)

  @staticmethod
  def getLastKeyForUser(username):
    """Helper function that returns the last possible key a user could own.

    This is useful for table scanning, in conjunction with getFirstKeyForUser.

    Args:
      username: The given user's e-mail address.
    Returns:
      The internal key representing the last possible key that a user could
      own (although the value of this key is not able to be used for actual
      user data).
    """

    return db.Key.from_path("FileMetadata", username + FileMetadata.__NEXT)

  @staticmethod
  def getKeyName(username, date, blob_key):
    """Returns the internal key for a particular item in the database.

    Our items are stored with keys of the form 'user/date/blob_key' ('/' is
    not the real separator, but __SEP is).

    Args:
      username: The given user's e-mail address.
      date: A datetime object representing the date and time that an input
        file was uploaded to this app.
      blob_key: The blob key corresponding to the location of the input file
        in the Blobstore.
    Returns:
      The internal key for the item specified by (username, date, blob_key).
    """

    sep = FileMetadata.__SEP
    return str(username + sep + str(date) + sep + blob_key)


class IndexHandler(webapp2.RequestHandler):
  """The main page that users will interact with, which presents users with
  the ability to upload new data or run MapReduce jobs on their existing data.
  """

  template_env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"),
                                    autoescape=True)

  def get(self):
    user = users.get_current_user()
    username = user.nickname()

    first = FileMetadata.getFirstKeyForUser(username)
    last = FileMetadata.getLastKeyForUser(username)

    q = FileMetadata.all()
    q.filter("__key__ >", first)
    q.filter("__key__ < ", last)
    results = q.fetch(10)

    items = [result for result in results]
    length = len(items)

    bucket_name = app_identity.get_default_gcs_bucket_name()
    upload_url = blobstore.create_upload_url("/upload",
                                             gs_bucket_name=bucket_name)

    self.response.out.write(self.template_env.get_template("index.html").render(
        {"username": username,
         "items": items,
         "length": length,
         "upload_url": upload_url}))

  def post(self):
    filekey = self.request.get("filekey")
    blob_key = self.request.get("blobkey")

    if self.request.get("song_sold_num"):
      pipeline = SongSoldNumPipeline(filekey, blob_key)
    elif self.request.get("dollar_song"):
      pipeline = DollarSongPipeline(filekey, blob_key)
    elif self.request.get("song_artist"):
      pipeline = SongArtistPipeline(filekey, blob_key)
    elif self.request.get("dollar_artist"):
      pipeline = DollarArtistPipeline(filekey, blob_key)
    elif self.request.get("jazz_song_sold_num"):
      pipeline = JazzSongSoldNumPipeline(filekey, blob_key)
    elif self.request.get("jazz_dollar_song"):
      pipeline = JazzDollarSongPipeline(filekey, blob_key)
    elif self.request.get("jazz_song_artist"):
      pipeline = JazzSongArtistPipeline(filekey, blob_key)
    elif self.request.get("jazz_dollar_artist"):
      pipeline = JazzDollarArtistPipeline(filekey, blob_key)
    else:
      pipeline = MostBuyTogetherPipeline(filekey, blob_key)

    pipeline.start()
    self.redirect(pipeline.base_path + "/status?root=" + pipeline.pipeline_id)

def transaction_into_sentences(s):
  return s.split("\n")

def transaction_into_fields(s):
  return s.split("\t")

def split_into_sentences(s):
  """Split text into list of sentences."""
  s = re.sub(r"\s+", " ", s)
  s = re.sub(r"[\\.\\?\\!]", "\n", s)
  return s.split("\n")


def split_into_words(s):
  """Split a sentence into list of words."""
  s = re.sub(r"\W+", " ", s)
  s = re.sub(r"[_0-9]+", " ", s)
  return s.split()


# Count each song sold number map and reduce function
def song_sold_num_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    w = [words[2], words[3], words[4]];
    w = "-".join(w)
    yield (w, "")

def song_sold_num_reduce(key, values):
  a = key.split("-")
  yield "%s: %d\n" % (a[0], len(values))


# Calculate the total dollar for each song map and reduce function
def dollar_song_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    w = [words[2], words[3], words[4]];
    w = "-".join(w)
    yield (w, words[7])

def dollar_song_reduce(key, values):
  a = key.split("-")
  sum_price = 0.0
  for price in values:
    sum_price = sum_price + float(price)
  yield "%s: %.2f\n" % (a[0], sum_price)


# Count the number of songs sold for each artist
def song_artist_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    yield (words[3], "")

def song_artist_reduce(key, values):
  yield "%s: %d\n" % (key, len(values))


# Calculate the total dollar amount of sales for each artist
def dollar_artist_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    yield (words[3], words[7])

def dollar_artist_reduce(key, values):
  sum_price = 0.0
  for price in values:
    sum_price = sum_price + float(price)
  yield "%s: %.2f\n" % (key, sum_price)


# Count each song sold number map and reduce function for Jazz
def jazz_song_sold_num_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    if words[5] == "Jazz":
      w = [words[2], words[3], words[4]];
      w = "-".join(w)
      yield (w, "")

def jazz_song_sold_num_reduce(key, values):
  a = key.split("-")
  yield "%s: %d\n" % (a[0], len(values))


# Calculate the total dollar for each song map and reduce function for Jazz
def jazz_dollar_song_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    if words[5] == "Jazz":
      w = [words[2], words[3], words[4]];
      w = "-".join(w)
      yield (w, words[7])

def jazz_dollar_song_reduce(key, values):
  a = key.split("-")
  sum_price = 0.0
  for price in values:
    sum_price = sum_price + float(price)
  yield "%s: %.2f\n" % (a[0], sum_price)



# Count the number of songs sold for each artist for Jazz
def jazz_song_artist_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    if words[5] == "Jazz":
      yield (words[3], "")

def jazz_song_artist_reduce(key, values):
  yield "%s: %d\n" % (key, len(values))


# Calculate the total dollar amount of sales for each artist for Jazz
def jazz_dollar_artist_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    if words[5] == "Jazz":
      yield (words[3], words[7])

def jazz_dollar_artist_reduce(key, values):
  sum_price = 0.0
  for price in values:
    sum_price = sum_price + float(price)
  yield "%s: %.2f\n" % (key, sum_price)


# find the other song that was purchased most often at the same time
# and count how many times the two songs were purchased together
def songs_same_time_map(data):
  (entry, text_fn) = data
  text = text_fn()

  logging.debug("Got %s", entry.filename)
  for s in transaction_into_sentences(text):
    words = transaction_into_fields(s)
    sametime = [words[0], words[1]]
    song = [words[2], words[3], words[4]]
    sametime = "-".join(sametime)
    song = "-".join(song)
    yield (sametime, song)

def songs_same_time_reduce(key, values):
  for v in values:
    for other in values:
      if v != other:
        yield "%s\t%s\n" % (v, other)

def most_buy_together_map(data):
  while(data._remaining()):
    text_fn = data.readline()
    text_fn = text_fn[:-1]
    words = transaction_into_fields(text_fn)
    yield (words[0], words[1])

def most_buy_together_reduce(key, values):
  song_list = {}
  for v in values:
    if v in song_list:
      song_list[v] = song_list[v] + 1
    else:
      song_list[v] = 1
  target_song = max(song_list.iteritems(), key=operator.itemgetter(1))[0]
  yield "%s, %s, %d\n" % (key.split("-")[0], target_song.split("-")[0], song_list[target_song])


class SongSoldNumPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "song_sold_num",
        "main.song_sold_num_map",
        "main.song_sold_num_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("SongSoldNum", filekey, output)

class DollarSongPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "dollar_song",
        "main.dollar_song_map",
        "main.dollar_song_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("DollarSong", filekey, output)


class SongArtistPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "song_artist",
        "main.song_artist_map",
        "main.song_artist_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("SongArtist", filekey, output)

class DollarArtistPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "dollar_artist",
        "main.dollar_artist_map",
        "main.dollar_artist_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("DollarArtist", filekey, output)

class JazzSongSoldNumPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "jazz_song_sold_num",
        "main.jazz_song_sold_num_map",
        "main.jazz_song_sold_num_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("JazzSongSoldNum", filekey, output)

class JazzDollarSongPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "jazz_dollar_song",
        "main.jazz_dollar_song_map",
        "main.jazz_dollar_song_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("JazzDollarSong", filekey, output)


class JazzSongArtistPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "jazz_song_artist",
        "main.jazz_song_artist_map",
        "main.jazz_song_artist_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("JazzSongArtist", filekey, output)

class JazzDollarArtistPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()
    output = yield mapreduce_pipeline.MapreducePipeline(
        "jazz_dollar_artist",
        "main.jazz_dollar_artist_map",
        "main.jazz_dollar_artist_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)
    yield StoreOutput("JazzDollarArtist", filekey, output)


class GCSMapperParams(base_handler.PipelineBase):

  def run(self, GCSPath):
      bucket_name = app_identity.get_default_gcs_bucket_name()

      return {
        "input_reader": {
        "bucket_name": bucket_name,
        "objects": [path.split('/', 2)[2] for path in GCSPath],
        }
      }

class MostBuyTogetherPipeline(base_handler.PipelineBase):

  def run(self, filekey, blobkey):
    bucket_name = app_identity.get_default_gcs_bucket_name()

    deduped_blob_key = yield mapreduce_pipeline.MapreducePipeline(
        "songs_same_time",
        "main.songs_same_time_map",
        "main.songs_same_time_reduce",
        "mapreduce.input_readers.BlobstoreZipInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params={
            "blob_key": blobkey,
        },
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)

    output = yield mapreduce_pipeline.MapreducePipeline(
        "most_buy_together",
        "main.most_buy_together_map",
        "main.most_buy_together_reduce",
        "mapreduce.input_readers.GoogleCloudStorageInputReader",
        "mapreduce.output_writers.GoogleCloudStorageOutputWriter",
        mapper_params=(yield GCSMapperParams(deduped_blob_key)),
        reducer_params={
            "output_writer": {
                "bucket_name": bucket_name,
                "content_type": "text/plain",
            }
        },
        shards=4)

    yield StoreOutput("MostBuyTogether", filekey, output)

class StoreOutput(base_handler.PipelineBase):
  """A pipeline to store the result of the MapReduce job in the database.

  Args:
    mr_type: the type of mapreduce job run (e.g., WordCount, Index)
    encoded_key: the DB key corresponding to the metadata of this job
    output: the gcs file path where the output of the job is stored
  """

  def run(self, mr_type, encoded_key, output):
    logging.debug("output is %s" % str(output))
    key = db.Key(encoded=encoded_key)
    m = FileMetadata.get(key)

    blobstore_filename = "/gs" + output[0]
    blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
    url_path = "/blobstore/" + blobstore_gs_key

    if mr_type == "SongSoldNum":
      m.songsoldnum_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.songsoldnum_link1 = url_path
        elif i == 2:
          m.songsoldnum_link2 = url_path
        else:
          m.songsoldnum_link3 = url_path
    elif mr_type == "DollarSong":
      m.dollarsong_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.dollarsong_link1 = url_path
        elif i == 2:
          m.dollarsong_link2 = url_path
        else:
          m.dollarsong_link3 = url_path
    elif mr_type == "SongArtist":
      m.songartist_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.songartist_link1 = url_path
        elif i == 2:
          m.songartist_link2 = url_path
        else:
          m.songartist_link3 = url_path
    elif mr_type == "DollarArtist":
      m.dollarartist_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.dollarartist_link1 = url_path
        elif i == 2:
          m.dollarartist_link2 = url_path
        else:
          m.dollarartist_link3 = url_path
    elif mr_type == "JazzSongSoldNum":
      m.jazzsongsoldnum_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.jazzsongsoldnum_link1 = url_path
        elif i == 2:
          m.jazzsongsoldnum_link2 = url_path
        else:
          m.jazzsongsoldnum_link3 = url_path
    elif mr_type == "JazzDollarSong":
      m.jazzdollarsong_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.jazzdollarsong_link1 = url_path
        elif i == 2:
          m.jazzdollarsong_link2 = url_path
        else:
          m.jazzdollarsong_link3 = url_path
    elif mr_type == "JazzSongArtist":
      m.jazzsongartist_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.jazzsongartist_link1 = url_path
        elif i == 2:
          m.jazzsongartist_link2 = url_path
        else:
          m.jazzsongartist_link3 = url_path
    elif mr_type == "JazzDollarArtist":
      m.jazzdollarartist_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.jazzdollarartist_link1 = url_path
        elif i == 2:
          m.jazzdollarartist_link2 = url_path
        else:
          m.jazzdollarartist_link3 = url_path
    else:
      m.mostbuytogether_link = url_path
      for i in range(1, len(output)):
        blobstore_filename = "/gs" + output[i]
        blobstore_gs_key = blobstore.create_gs_key(blobstore_filename)
        url_path = "/blobstore/" + blobstore_gs_key
        if i == 1:
          m.mostbuytogether_link1 = url_path
        elif i == 2:
          m.mostbuytogether_link2 = url_path
        else:
          m.mostbuytogether_link3 = url_path

    m.put()

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  """Handler to upload data to blobstore."""

  def post(self):
    source = "uploaded by user"
    upload_files = self.get_uploads("file")
    blob_key = upload_files[0].key()
    name = self.request.get("name")

    user = users.get_current_user()

    username = user.nickname()
    date = datetime.datetime.now()
    str_blob_key = str(blob_key)
    key = FileMetadata.getKeyName(username, date, str_blob_key)

    m = FileMetadata(key_name = key)
    m.owner = user
    m.filename = name
    m.uploadedOn = date
    m.source = source
    m.blobkey = str_blob_key
    m.put()

    self.redirect("/")


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
  """Handler to download blob by blobkey."""

  def get(self, key):
    key = str(urllib.unquote(key)).strip()
    logging.debug("key is %s" % key)
    self.send_blob(key)


app = webapp2.WSGIApplication(
    [
        ('/', IndexHandler),
        ('/upload', UploadHandler),
        (r'/blobstore/(.*)', DownloadHandler),
    ],
    debug=True)
