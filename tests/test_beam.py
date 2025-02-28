import os
import tempfile
from unittest import TestCase

import apache_beam as beam

import nlp


class DummyBeamDataset(nlp.BeamBasedBuilder):
    """Dummy beam dataset."""

    def _info(self):
        return nlp.DatasetInfo(
            features=nlp.Features({"content": nlp.Value("string")}),
            # No default supervised_keys.
            supervised_keys=None,
        )

    def _split_generators(self, dl_manager, pipeline):
        return [nlp.SplitGenerator(name=nlp.Split.TRAIN, gen_kwargs={"examples": get_test_dummy_examples()})]

    def _build_pcollection(self, pipeline, examples):
        return pipeline | "Load Examples" >> beam.Create(examples)


class NestedBeamDataset(nlp.BeamBasedBuilder):
    """Dummy beam dataset."""

    def _info(self):
        return nlp.DatasetInfo(
            features=nlp.Features({"a": nlp.Sequence({"b": nlp.Value("string")})}),
            # No default supervised_keys.
            supervised_keys=None,
        )

    def _split_generators(self, dl_manager, pipeline):
        return [nlp.SplitGenerator(name=nlp.Split.TRAIN, gen_kwargs={"examples": get_test_nested_examples()})]

    def _build_pcollection(self, pipeline, examples):
        return pipeline | "Load Examples" >> beam.Create(examples)


def get_test_dummy_examples():
    return [(i, {"content": content}) for i, content in enumerate(["foo", "bar", "foobar"])]


def get_test_nested_examples():
    return [(i, {"a": {"b": [content]}}) for i, content in enumerate(["foo", "bar", "foobar"])] * 10_000


class BeamBuilderTest(TestCase):
    def test_download_and_prepare(self):
        expected_num_examples = len(get_test_dummy_examples())
        with tempfile.TemporaryDirectory() as tmp_cache_dir:
            builder = DummyBeamDataset(cache_dir=tmp_cache_dir, beam_runner="DirectRunner")
            builder.download_and_prepare()
            dset = builder.as_dataset()
            self.assertEqual(dset["train"].num_rows, expected_num_examples)
            self.assertEqual(dset["train"].info.splits["train"].num_examples, expected_num_examples)
            self.assertDictEqual(dset["train"][0], get_test_dummy_examples()[0][1])
            self.assertDictEqual(
                dset["train"][expected_num_examples - 1], get_test_dummy_examples()[expected_num_examples - 1][1]
            )
            self.assertTrue(
                os.path.exists(
                    os.path.join(tmp_cache_dir, "dummy_beam_dataset", "default", "0.0.0", "dataset_info.json")
                )
            )

    def test_no_beam_options(self):
        with tempfile.TemporaryDirectory() as tmp_cache_dir:
            builder = DummyBeamDataset(cache_dir=tmp_cache_dir)
            self.assertRaises(nlp.builder.MissingBeamOptions, builder.download_and_prepare)

    def test_nested_features(self):
        expected_num_examples = len(get_test_nested_examples())
        with tempfile.TemporaryDirectory() as tmp_cache_dir:
            builder = NestedBeamDataset(cache_dir=tmp_cache_dir, beam_runner="DirectRunner")
            builder.download_and_prepare()
            dset = builder.as_dataset()
            self.assertEqual(dset["train"].num_rows, expected_num_examples)
            self.assertEqual(dset["train"].info.splits["train"].num_examples, expected_num_examples)
            self.assertDictEqual(dset["train"][0], get_test_nested_examples()[0][1])
            self.assertDictEqual(
                dset["train"][expected_num_examples - 1], get_test_nested_examples()[expected_num_examples - 1][1]
            )
            self.assertTrue(
                os.path.exists(
                    os.path.join(tmp_cache_dir, "nested_beam_dataset", "default", "0.0.0", "dataset_info.json")
                )
            )
