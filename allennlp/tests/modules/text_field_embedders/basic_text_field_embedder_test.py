import pytest
import torch

from allennlp.common import Params
from allennlp.common.checks import ConfigurationError
from allennlp.data import Vocabulary
from allennlp.modules.text_field_embedders import BasicTextFieldEmbedder
from allennlp.common.testing import AllenNlpTestCase


class TestBasicTextFieldEmbedder(AllenNlpTestCase):
    def setUp(self):
        super().setUp()
        self.vocab = Vocabulary()
        self.vocab.add_token_to_namespace("1")
        self.vocab.add_token_to_namespace("2")
        self.vocab.add_token_to_namespace("3")
        self.vocab.add_token_to_namespace("4")
        params = Params(
            {
                "token_embedders": {
                    "words1": {"type": "embedding", "embedding_dim": 2},
                    "words2": {"type": "embedding", "embedding_dim": 5},
                    "words3": {"type": "embedding", "embedding_dim": 3},
                }
            }
        )
        self.token_embedder = BasicTextFieldEmbedder.from_params(vocab=self.vocab, params=params)
        self.inputs = {
            "words1": {"tokens": torch.LongTensor([[0, 2, 3, 5]])},
            "words2": {"tokens": torch.LongTensor([[1, 4, 3, 2]])},
            "words3": {"tokens": torch.LongTensor([[1, 5, 1, 2]])},
        }

    def test_get_output_dim_aggregates_dimension_from_each_embedding(self):
        assert self.token_embedder.get_output_dim() == 10

    def test_forward_asserts_input_field_match(self):
        # Total mismatch
        self.inputs["words4"] = self.inputs["words3"]
        del self.inputs["words3"]
        with pytest.raises(ConfigurationError) as exc:
            self.token_embedder(self.inputs)
        assert exc.match("Mismatched token keys")

        self.inputs["words3"] = self.inputs["words4"]

        # Text field has too many inputs
        with pytest.raises(ConfigurationError) as exc:
            self.token_embedder(self.inputs)
        assert exc.match("Mismatched token keys")

        del self.inputs["words4"]

    def test_forward_concats_resultant_embeddings(self):
        assert self.token_embedder(self.inputs).size() == (1, 4, 10)

    def test_forward_works_on_higher_order_input(self):
        params = Params(
            {
                "token_embedders": {
                    "words": {"type": "embedding", "num_embeddings": 20, "embedding_dim": 2},
                    "characters": {
                        "type": "character_encoding",
                        "embedding": {"embedding_dim": 4, "num_embeddings": 15},
                        "encoder": {
                            "type": "cnn",
                            "embedding_dim": 4,
                            "num_filters": 10,
                            "ngram_filter_sizes": [3],
                        },
                    },
                }
            }
        )
        token_embedder = BasicTextFieldEmbedder.from_params(vocab=self.vocab, params=params)
        inputs = {
            "words": {"tokens": (torch.rand(3, 4, 5, 6) * 20).long()},
            "characters": {"token_characters": (torch.rand(3, 4, 5, 6, 7) * 15).long()},
        }
        assert token_embedder(inputs, num_wrapping_dims=2).size() == (3, 4, 5, 6, 12)

    def test_forward_runs_with_forward_params(self):
        elmo_fixtures_path = self.FIXTURES_ROOT / "elmo_multilingual" / "es"
        options_file = str(elmo_fixtures_path / "options.json")
        weight_file = str(elmo_fixtures_path / "weights.hdf5")
        params = Params(
            {
                "token_embedders": {
                    "elmo": {
                        "type": "elmo_token_embedder_multilang",
                        "options_files": {"es": options_file},
                        "weight_files": {"es": weight_file},
                    }
                }
            }
        )
        token_embedder = BasicTextFieldEmbedder.from_params(vocab=self.vocab, params=params)
        inputs = {"elmo": {"tokens": (torch.rand(3, 6, 50) * 15).long()}}
        kwargs = {"lang": "es"}
        token_embedder(inputs, **kwargs)

    def test_forward_runs_with_non_bijective_mapping(self):
        elmo_fixtures_path = self.FIXTURES_ROOT / "elmo"
        options_file = str(elmo_fixtures_path / "options.json")
        weight_file = str(elmo_fixtures_path / "lm_weights.hdf5")
        params = Params(
            {
                "token_embedders": {
                    "words": {"type": "embedding", "num_embeddings": 20, "embedding_dim": 2},
                    "elmo": {
                        "type": "elmo_token_embedder",
                        "options_file": options_file,
                        "weight_file": weight_file,
                    },
                }
            }
        )
        token_embedder = BasicTextFieldEmbedder.from_params(vocab=self.vocab, params=params)
        inputs = {
            "words": {"tokens": (torch.rand(3, 6) * 20).long()},
            "elmo": {"tokens": (torch.rand(3, 6, 50) * 15).long()},
        }
        token_embedder(inputs)

    def test_forward_runs_with_non_bijective_mapping_with_null(self):
        elmo_fixtures_path = self.FIXTURES_ROOT / "elmo"
        options_file = str(elmo_fixtures_path / "options.json")
        weight_file = str(elmo_fixtures_path / "lm_weights.hdf5")
        params = Params(
            {
                "token_embedders": {
                    "elmo": {
                        "type": "elmo_token_embedder",
                        "options_file": options_file,
                        "weight_file": weight_file,
                    }
                }
            }
        )
        token_embedder = BasicTextFieldEmbedder.from_params(vocab=self.vocab, params=params)
        inputs = {"elmo": {"tokens": (torch.rand(3, 6, 50) * 15).long()}}
        token_embedder(inputs)

    def test_forward_runs_with_non_bijective_mapping_with_dict(self):
        elmo_fixtures_path = self.FIXTURES_ROOT / "elmo"
        options_file = str(elmo_fixtures_path / "options.json")
        weight_file = str(elmo_fixtures_path / "lm_weights.hdf5")
        params = Params(
            {
                "token_embedders": {
                    "words": {"type": "embedding", "num_embeddings": 20, "embedding_dim": 2},
                    "elmo": {
                        "type": "elmo_token_embedder",
                        "options_file": options_file,
                        "weight_file": weight_file,
                    },
                }
            }
        )
        token_embedder = BasicTextFieldEmbedder.from_params(vocab=self.vocab, params=params)
        inputs = {
            "words": {"tokens": (torch.rand(3, 6) * 20).long()},
            "elmo": {"tokens": (torch.rand(3, 6, 50) * 15).long()},
        }
        token_embedder(inputs)

    def test_forward_runs_with_bijective_and_non_bijective_mapping(self):
        params = Params(
            {
                "token_embedders": {
                    "bert": {"type": "bert-pretrained", "pretrained_model": "bert-base-uncased"},
                    "token_characters": {
                        "type": "character_encoding",
                        "embedding": {"embedding_dim": 5},
                        "encoder": {
                            "type": "cnn",
                            "embedding_dim": 5,
                            "num_filters": 5,
                            "ngram_filter_sizes": [5],
                        },
                    },
                }
            }
        )
        token_embedder = BasicTextFieldEmbedder.from_params(vocab=self.vocab, params=params)
        inputs = {
            "bert": {
                "input_ids": (torch.rand(3, 5) * 10).long(),
                "offsets": (torch.rand(3, 5) * 1).long(),
            },
            "token_characters": {"token_characters": (torch.rand(3, 5, 5) * 1).long()},
        }
        token_embedder(inputs)
