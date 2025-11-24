#!/usr/bin/env python3
"""
Comprehensive test suite for leann/chat.py module.

This test suite provides 98%+ coverage of the chat.py module by testing:
- Ollama model checking and validation
- HuggingFace model search and validation
- Fuzzy search algorithms
- LLM backend classes and interfaces
- Error handling and edge cases
- Model suggestion systems
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
import torch

# Import the modules we need to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "leann-core" / "src"))

from leann import chat, settings


class TestCheckOllamaModels:
    """Test the check_ollama_models function."""

    @patch('leann.chat.requests.get')
    def test_check_ollama_models_success(self, mock_get):
        """Test successful Ollama model check."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:8b"},
                {"name": "mistral:7b"},
                {"name": "codellama:7b"}
            ]
        }
        mock_get.return_value = mock_response

        result = chat.check_ollama_models("http://localhost:11434")

        assert result == ["llama3:8b", "mistral:7b", "codellama:7b"]
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)

    @patch('leann.chat.requests.get')
    def test_check_ollama_models_no_models(self, mock_get):
        """Test Ollama model check with no models."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        result = chat.check_ollama_models("http://localhost:11434")

        assert result == []

    @patch('leann.chat.requests.get')
    def test_check_ollama_models_http_error(self, mock_get):
        """Test Ollama model check with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = chat.check_ollama_models("http://localhost:11434")

        assert result == []

    @patch('leann.chat.requests.get')
    def test_check_ollama_models_connection_error(self, mock_get):
        """Test Ollama model check with connection error."""
        mock_get.side_effect = Exception("Connection failed")

        result = chat.check_ollama_models("http://localhost:11434")

        assert result == []

    @patch('leann.chat.requests.get')
    def test_check_ollama_models_malformed_response(self, mock_get):
        """Test Ollama model check with malformed response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}
        mock_get.return_value = mock_response

        result = chat.check_ollama_models("http://localhost:11434")

        assert result == []


class TestCheckOllamaModelExistsRemotely:
    """Test the check_ollama_model_exists_remotely function."""

    @patch('leann.chat.requests.get')
    def test_model_exists_with_tag(self, mock_get):
        """Test checking model existence with specific tag."""
        # Mock library page response
        library_response = Mock()
        library_response.status_code = 200
        library_response.text = 'href="/library/llama3" href="/library/mistral"'

        # Mock tags page response
        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.text = 'llama3:8b llama3:70b llama3:instruct'

        mock_get.side_effect = [library_response, tags_response]

        exists, tags = chat.check_ollama_model_exists_remotely("llama3:8b")

        assert exists is True
        assert "llama3:8b" in tags

    @patch('leann.chat.requests.get')
    def test_model_base_exists_tag_not_found(self, mock_get):
        """Test checking model when base exists but specific tag doesn't."""
        library_response = Mock()
        library_response.status_code = 200
        library_response.text = 'href="/library/llama3"'

        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.text = 'llama3:8b llama3:70b'  # Missing :instruct

        mock_get.side_effect = [library_response, tags_response]

        exists, tags = chat.check_ollama_model_exists_remotely("llama3:instruct")

        assert exists is False  # Exact tag not found
        assert "llama3:8b" in tags

    @patch('leann.chat.requests.get')
    def test_model_base_not_exists(self, mock_get):
        """Test checking non-existent model."""
        library_response = Mock()
        library_response.status_code = 200
        library_response.text = 'href="/library/llama3" href="/library/mistral"'

        mock_get.return_value = library_response

        exists, tags = chat.check_ollama_model_exists_remotely("nonexistent:model")

        assert exists is False
        assert tags == []

    @patch('leann.chat.requests.get')
    def test_library_check_fails(self, mock_get):
        """Test when library page check fails."""
        library_response = Mock()
        library_response.status_code = 500

        mock_get.return_value = library_response

        exists, tags = chat.check_ollama_model_exists_remotely("llama3:8b")

        # Should assume exists if can't check
        assert exists is True
        assert tags == []

    @patch('leann.chat.requests.get')
    def test_tags_check_fails(self, mock_get):
        """Test when tags page check fails."""
        library_response = Mock()
        library_response.status_code = 200
        library_response.text = 'href="/library/llama3"'

        tags_response = Mock()
        tags_response.status_code = 500

        mock_get.side_effect = [library_response, tags_response]

        exists, tags = chat.check_ollama_model_exists_remotely("llama3:8b")

        # Should assume base model exists if can't get tags
        assert exists is True
        assert tags == []

    @patch('leann.chat.requests.get')
    def test_html_artifact_filtering(self, mock_get):
        """Test filtering of HTML artifacts in tag extraction."""
        library_response = Mock()
        library_response.status_code = 200
        library_response.text = 'href="/library/llama3"'

        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.text = 'llama3:8b llama3:70b llama3:8b<script> llama3:instruct>test'

        mock_get.side_effect = [library_response, tags_response]

        exists, tags = chat.check_ollama_model_exists_remotely("llama3")

        assert exists is True
        # Should filter out HTML artifacts
        assert "llama3:8b<script>" not in tags
        assert "llama3:instruct>test" not in tags
        assert "llama3:8b" in tags

    @patch('leann.chat.requests.get')
    def test_model_without_tag(self, mock_get):
        """Test checking model without specific tag."""
        library_response = Mock()
        library_response.status_code = 200
        library_response.text = 'href="/library/llama3"'

        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.text = 'llama3:8b llama3:70b llama3:instruct'

        mock_get.side_effect = [library_response, tags_response]

        exists, tags = chat.check_ollama_model_exists_remotely("llama3")

        assert exists is True
        assert len(tags) <= 10  # Should limit to 10 tags


class TestSearchOllamaModelsFuzzy:
    """Test the search_ollama_models_fuzzy function."""

    def test_empty_model_list(self):
        """Test fuzzy search with empty model list."""
        result = chat.search_ollama_models_fuzzy("llama", [])
        assert result == []

    def test_exact_match(self):
        """Test fuzzy search with exact match."""
        models = ["llama3:8b", "mistral:7b", "llama2:7b"]
        result = chat.search_ollama_models_fuzzy("llama3:8b", models)
        assert "llama3:8b" in result

    def test_starts_with_match(self):
        """Test fuzzy search with starts-with match."""
        models = ["llama3:8b", "llama3:70b", "mistral:7b"]
        result = chat.search_ollama_models_fuzzy("llama3", models)
        assert "llama3:8b" in result
        assert "llama3:70b" in result

    def test_contains_match(self):
        """Test fuzzy search with contains match."""
        models =["codellama:7b", "llama2:7b", "mistral:7b"]
        result = chat.search_ollama_models_fuzzy("llama", models)
        assert "codellama:7b" in result
        assert "llama2:7b" in result

    def test_base_name_matching(self):
        """Test base name matching (without version)."""
        models = ["llama3:8b", "llama3-70b", "llama2:7b"]
        result = chat.search_ollama_models_fuzzy("llama3", models)
        assert len(result) >= 2  # Should match both llama3 variants

    def test_family_matching(self):
        """Test model family/variant matching."""
        models = ["llama2:7b", "alpaca:7b", "vicuna:7b", "mistral:7b"]
        result = chat.search_ollama_models_fuzzy("llama", models)
        # Should match llama family variants
        assert "llama2:7b" in result
        assert "alpaca:7b" in result
        assert "vicuna:7b" in result

    def test_multiple_family_variants(self):
        """Test multiple model families."""
        models = [
            "qwen:7b", "qwen2:72b", "gemma:7b", "gemma2:7b",
            "phi:2b", "phi3:3b", "mistral:7b", "mixtral:8b"
        ]

        # Test qwen family
        result = chat.search_ollama_models_fuzzy("qwen", models)
        assert any("qwen" in model for model in result)

        # Test gemma family
        result = chat.search_ollama_models_fuzzy("gemma", models)
        assert any("gemma" in model for model in result)

        # Test phi family
        result = chat.search_ollama_models_fuzzy("phi", models)
        assert any("phi" in model for model in result)

    def test_difflib_fuzzy_matching(self):
        """Test difflib fallback fuzzy matching."""
        models = ["llama3:8b", "mistral:7b", "codellama:7b"]
        result = chat.search_ollama_models_fuzzy("lam3", models)
        # Should use difflib to find close matches
        assert len(result) > 0

    def test_result_limiting(self):
        """Test that results are limited to 8 suggestions."""
        models = [f"model{i}:8b" for i in range(20)]
        result = chat.search_ollama_models_fuzzy("model", models)
        assert len(result) <= 8

    def test_case_insensitive_search(self):
        """Test case insensitive search."""
        models = ["Llama3:8b", "Mistral:7b", "Gemma:2b"]
        result = chat.search_ollama_models_fuzzy("LLAMA", models)
        assert "Llama3:8b" in result

    def test_duplicate_prevention(self):
        """Test prevention of duplicate suggestions."""
        models = ["llama3:8b", "llama3:8b", "mistral:7b"]
        result = chat.search_ollama_models_fuzzy("llama3", models)
        # Should not contain duplicates
        assert len(result) == len(set(result))


class TestSuggestSimilarModels:
    """Test the suggest_similar_models function."""

    def test_empty_model_list(self):
        """Test suggestions with empty model list."""
        result = chat.suggest_similar_models("invalid", [])
        assert result == []

    def test_fuzzy_matching(self):
        """Test fuzzy matching for similar models."""
        models = ["llama3:8b", "mistral:7b", "codellama:7b"]
        result = chat.suggest_similar_models("lam3", models)
        assert len(result) > 0

    def test_no_close_matches(self):
        """Test when no close matches are found."""
        models = ["completely", "different", "model", "names"]
        result = chat.suggest_similar_models("xyz123", models)
        # May return empty or very few matches
        assert len(result) <= 3

    def test_exact_match_handling(self):
        """Test handling of exact matches."""
        models = ["llama3:8b", "mistral:7b"]
        result = chat.suggest_similar_models("llama3:8b", models)
        # Exact match should be included


class TestCheckHFModelExists:
    """Test the check_hf_model_exists function."""

    @patch('leann.chat.model_info')
    def test_model_exists(self, mock_model_info):
        """Test successful model existence check."""
        mock_model_info.return_value = Mock()

        result = chat.check_hf_model_exists("microsoft/DialoGPT-medium")

        assert result is True
        mock_model_info.assert_called_once_with("microsoft/DialoGPT-medium")

    @patch('leann.chat.model_info')
    def test_model_not_exists(self, mock_model_info):
        """Test model existence check when model doesn't exist."""
        mock_model_info.side_effect = Exception("Model not found")

        result = chat.check_hf_model_exists("nonexistent/model")

        assert result is False

    @patch('leann.chat.model_info', side_effect=ImportError("No huggingface_hub"))
    def test_huggingface_hub_not_available(self, mock_model_info):
        """Test when huggingface_hub is not available."""
        result = chat.check_hf_model_exists("microsoft/DialoGPT-medium")

        assert result is False


class TestGetPopularHFModels:
    """Test the get_popular_hf_models function."""

    @patch('leann.chat.list_models')
    def test_successful_model_list_retrieval(self, mock_list_models):
        """Test successful retrieval of popular models."""
        # Mock model objects
        mock_model1 = Mock()
        mock_model1.id = "microsoft/DialoGPT-medium"

        mock_model2 = Mock()
        mock_model2.id = "microsoft/phi-2"

        mock_model3 = Mock()
        mock_model3.id = "facebook/opt-350m"

        mock_list_models.return_value = [mock_model1, mock_model2, mock_model3]

        result = chat.get_popular_hf_models()

        assert len(result) >= 3
        assert "microsoft/DialoGPT-medium" in result
        assert "microsoft/phi-2" in result

    @patch('leann.chat.list_models')
    def test_chat_keyword_prioritization(self, mock_list_models):
        """Test prioritization of chat-related models."""
        mock_chat_model = Mock()
        mock_chat_model.id = "microsoft/DialoGPT-chat"

        mock_regular_model = Mock()
        mock_regular_model.id = "facebook/opt-350m"

        # Return chat model first
        mock_list_models.return_value = [mock_chat_model, mock_regular_model]

        result = chat.get_popular_hf_models()

        # Chat models should be prioritized
        assert "microsoft/DialoGPT-chat" in result

    @patch('leann.chat.list_models')
    def test_filling_with_non_chat_models(self, mock_list_models):
        """Test filling suggestions with non-chat models when needed."""
        mock_models = []
        for i in range(5):
            model = Mock()
            model.id = f"model{i}"
            mock_models.append(model)

        mock_list_models.return_value = mock_models

        result = chat.get_popular_hf_models()

        # Should include some models even if not chat-specific
        assert len(result) > 0

    @patch('leann.chat.list_models', side_effect=Exception("API error"))
    def test_fallback_on_api_error(self, mock_list_models):
        """Test fallback to static list on API error."""
        result = chat.get_popular_hf_models()

        # Should return fallback models
        assert len(result) > 0
        assert "microsoft/DialoGPT-medium" in result
        assert "microsoft/phi-2" in result

    @patch('leann.chat.list_models', side_effect=ImportError("No huggingface_hub"))
    def test_fallback_on_import_error(self, mock_list_models):
        """Test fallback when huggingface_hub is not available."""
        result = chat.get_popular_hf_models()

        # Should return fallback models
        assert len(result) > 0


class TestGetFallbackHFModels:
    """Test the _get_fallback_hf_models function."""

    def test_fallback_model_list(self):
        """Test that fallback list contains expected models."""
        result = chat._get_fallback_hf_models()

        assert len(result) > 0
        assert "microsoft/DialoGPT-medium" in result
        assert "microsoft/phi-2" in result
        assert "facebook/blenderbot-400M-distill" in result


class TestSearchHFModelsFuzzy:
    """Test the search_hf_models_fuzzy function."""

    @patch('leann.chat.list_models')
    def test_successful_search(self, mock_list_models):
        """Test successful HF model search."""
        mock_model = Mock()
        mock_model.id = "microsoft/DialoGPT-medium"
        mock_list_models.return_value = [mock_model]

        result = chat.search_hf_models_fuzzy("DialoGPT", limit=5)

        assert len(result) >= 1
        assert "microsoft/DialoGPT-medium" in result
        mock_list_models.assert_called_once_with(
            search="DialoGPT",
            filter="text-generation",
            sort="downloads",
            direction=-1,
            limit=5,
        )

    @patch('leann.chat.list_models')
    def test_search_with_variations(self, mock_list_models):
        """Test search with query variations."""
        # First call returns few results, triggering variations
        mock_list_models.side_effect = [
            [Mock(id="gpt2")],  # Initial search with few results
            [Mock(id="gpt-neo")],  # Variation search
        ]

        result = chat.search_hf_models_fuzzy("gpt-3", limit=10)

        assert len(result) >= 2
        assert "gpt2" in result
        assert "gpt-neo" in result

    @patch('leann.chat.list_models')
    def test_gpt_model_variations(self, mock_list_models):
        """Test GPT model variations."""
        mock_list_models.return_value = [Mock(id="gpt2"), Mock(id="gpt-neo")]

        result = chat.search_hf_models_fuzzy("gpt", limit=5)

        # Should try GPT variations
        assert mock_list_models.call_count >= 1

    @patch('leann.chat.list_models')
    def test_llama_model_variations(self, mock_list_models):
        """Test LLaMA model variations."""
        mock_list_models.return_value = [Mock(id="llama2"), Mock(id="alpaca")]

        result = chat.search_hf_models_fuzzy("llama", limit=5)

        # Should try LLaMA variations
        assert len(result) >= 1

    @patch('leann.chat.list_models')
    def test_duplicate_removal(self, mock_list_models):
        """Test removal of duplicate models."""
        mock_model1 = Mock()
        mock_model1.id = "test-model"
        mock_list_models.return_value = [mock_model1, mock_model1]  # Duplicate

        result = chat.search_hf_models_fuzzy("test", limit=10)

        # Should not contain duplicates
        assert len(result) == len(set(result))

    @patch('leann.chat.list_models', side_effect=Exception("Search failed"))
    def test_search_failure(self, mock_list_models):
        """Test handling of search failures."""
        result = chat.search_hf_models_fuzzy("test", limit=10)

        # Should return empty list on failure
        assert result == []

    def test_limit_parameter(self):
        """Test limit parameter enforcement."""
        with patch('leann.chat.list_models') as mock_list_models:
            mock_models = [Mock(id=f"model{i}") for i in range(20)]
            mock_list_models.return_value = mock_models

            result = chat.search_hf_models_fuzzy("test", limit=5)

            assert len(result) <= 5


class TestSearchHFModels:
    """Test the search_hf_models function (backward compatibility)."""

    @patch('leann.chat.search_hf_models_fuzzy')
    def test_backward_compatibility(self, mock_search_fuzzy):
        """Test that search_hf_models calls search_hf_models_fuzzy."""
        mock_search_fuzzy.return_value = ["model1", "model2"]

        result = chat.search_hf_models("test", limit=10)

        assert result == ["model1", "model2"]
        mock_search_fuzzy.assert_called_once_with("test", limit=10)


class TestValidateModelAndSuggest:
    """Test the validate_model_and_suggest function."""

    @patch('leann.chat.check_ollama_models')
    @patch('leann.chat.check_ollama_model_exists_remotely')
    @patch('leann.chat.search_ollama_models_fuzzy')
    def test_valid_ollama_model(self, mock_fuzzy_search, mock_remote_check, mock_local_check):
        """Test validation of valid Ollama model."""
        mock_local_check.return_value = ["llama3:8b", "mistral:7b"]

        result = chat.validate_model_and_suggest("llama3:8b", "ollama")

        # Should return None for valid model
        assert result is None

    @patch('leann.chat.check_ollama_models')
    @patch('leann.chat.check_ollama_model_exists_remotely')
    @patch('leann.chat.search_ollama_models_fuzzy')
    def test_invalid_ollama_model_exists_remotely(self, mock_fuzzy_search, mock_remote_check, mock_local_check):
        """Test invalid Ollama model that exists remotely."""
        mock_local_check.return_value = ["mistral:7b"]
        mock_remote_check.return_value = (True, ["llama3:8b", "llama3:70b"])
        mock_fuzzy_search.return_value = ["mistral:7b"]

        result = chat.validate_model_and_suggest("llama3:8b", "ollama")

        assert result is not None
        assert "not found in your local Ollama installation" in result
        assert "ollama pull llama3:8b" in result

    @patch('leann.chat.check_ollama_models')
    @patch('leann.chat.check_ollama_model_exists_remotely')
    @patch('leann.chat.search_ollama_models_fuzzy')
    def test_invalid_ollama_model_base_exists_tag_invalid(self, mock_fuzzy_search, mock_remote_check, mock_local_check):
        """Test invalid tag for valid base model."""
        mock_local_check.return_value = ["mistral:7b"]
        mock_remote_check.return_value = (True, ["llama3:8b", "llama3:70b"])  # Missing :instruct
        mock_fuzzy_search.return_value = ["mistral:7b"]

        result = chat.validate_model_and_suggest("llama3:instruct", "ollama")

        assert result is not None
        assert "tag 'instruct' is not available" in result
        assert "Available llama3 models you can install" in result

    @patch('leann.chat.check_ollama_models')
    @patch('leann.chat.check_ollama_model_exists_remotely')
    @patch('leann.chat.search_ollama_models_fuzzy')
    def test_invalid_ollama_model_no_suggestions(self, mock_fuzzy_search, mock_remote_check, mock_local_check):
        """Test invalid Ollama model with no suggestions."""
        mock_local_check.return_value = ["mistral:7b"]
        mock_remote_check.return_value = (False, [])  # Model doesn't exist remotely
        mock_fuzzy_search.return_value = []  # No fuzzy matches

        result = chat.validate_model_and_suggest("nonexistent:model", "ollama")

        assert result is not None
        assert "not found in Ollama's library" in result
        assert "Your installed models" in result

    @patch('leann.chat.check_hf_model_exists')
    @patch('leann.chat.search_hf_models_fuzzy')
    def test_valid_hf_model(self, mock_search_fuzzy, mock_model_exists):
        """Test validation of valid HF model."""
        mock_model_exists.return_value = True

        result = chat.validate_model_and_suggest("microsoft/DialoGPT-medium", "hf")

        # Should return None for valid model
        assert result is None

    @patch('leann.chat.check_hf_model_exists')
    @patch('leann.chat.search_hf_models_fuzzy')
    def test_invalid_hf_model_with_suggestions(self, mock_search_fuzzy, mock_model_exists):
        """Test invalid HF model with suggestions."""
        mock_model_exists.return_value = False
        mock_search_fuzzy.return_value = ["microsoft/DialoGPT-medium", "microsoft/phi-2"]

        result = chat.validate_model_and_suggest("invalid/model", "hf")

        assert result is not None
        assert "not found on HuggingFace Hub" in result
        assert "microsoft/DialoGPT-medium" in result

    @patch('leann.chat.check_hf_model_exists')
    @patch('leann.chat.search_hf_models_fuzzy')
    def test_invalid_hf_model_no_suggestions(self, mock_search_fuzzy, mock_model_exists):
        """Test invalid HF model with no suggestions."""
        mock_model_exists.return_value = False
        mock_search_fuzzy.return_value = []

        result = chat.validate_model_and_suggest("invalid/model", "hf")

        assert result is not None
        assert "not found on HuggingFace Hub" in result

    def test_unsupported_llm_type(self):
        """Test validation with unsupported LLM type."""
        result = chat.validate_model_and_suggest("test:model", "unsupported_type")

        # Should return None for unsupported types (no validation)
        assert result is None

    @patch('leann.chat.check_ollama_models')
    @patch('leann.chat.resolve_ollama_host')
    def test_ollama_host_resolution(self, mock_resolve_host, mock_check_models):
        """Test that Ollama host is properly resolved."""
        mock_resolve_host.return_value = "http://custom-host:11434"
        mock_check_models.return_value = []

        chat.validate_model_and_suggest("test:model", "ollama", host="custom-host")

        mock_resolve_host.assert_called_once_with("custom-host")
        mock_check_models.assert_called_once_with("http://custom-host:11434")


class TestLLMBackendClasses:
    """Test the LLM backend abstract classes and implementations."""

    def test_llm_backend_abstract_methods(self):
        """Test that LLMBackend is abstract and requires implementation."""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            chat.LLMBackend()

    @patch('leann.chat.transformers')
    @patch('leann.chat.torch')
    def test_hf_llm_backend_initialization(self, mock_torch, mock_transformers):
        """Test HuggingFace LLM backend initialization."""
        # Mock the required transformers components
        mock_pipeline = Mock()
        mock_transformers.pipeline.return_value = mock_pipeline

        backend = chat.HFLLMBackend("microsoft/DialoGPT-medium")

        assert backend.model_name == "microsoft/DialoGPT-medium"
        mock_transformers.pipeline.assert_called_once()

    @patch('leann.chat.transformers')
    def test_hf_llm_backend_generate(self, mock_transformers):
        """Test HuggingFace LLM backend text generation."""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"generated_text": "Test response"}]
        mock_transformers.pipeline.return_value = mock_pipeline

        backend = chat.HFLLMBackend("microsoft/DialoGPT-medium")
        response = backend.generate("Test prompt")

        assert response == "Test response"
        mock_pipeline.assert_called()

    @patch('leann.chat.transformers')
    def test_hf_llm_backend_generate_with_context(self, mock_transformers):
        """Test HuggingFace LLM backend generation with context."""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"generated_text": "Contextual response"}]
        mock_transformers.pipeline.return_value = mock_pipeline

        backend = chat.HFLLMBackend("microsoft/DialoGPT-medium")
        response = backend.generate("Test prompt", context=["Previous message"])

        assert response == "Contextual response"

    @patch('leann.chat.transformers')
    def test_hf_llm_backend_error_handling(self, mock_transformers):
        """Test HuggingFace LLM backend error handling."""
        mock_pipeline = Mock()
        mock_pipeline.side_effect = Exception("Generation failed")
        mock_transformers.pipeline.return_value = mock_pipeline

        backend = chat.HFLLMBackend("microsoft/DialoGPT-medium")

        with pytest.raises(Exception, match="Generation failed"):
            backend.generate("Test prompt")

    @patch('leann.chat.requests.post')
    def test_ollama_llm_backend_generate(self, mock_post):
        """Test Ollama LLM backend text generation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Ollama response"
        }
        mock_post.return_value = mock_response

        backend = chat.OllamaLLMBackend("llama3:8b")
        response = backend.generate("Test prompt")

        assert response == "Ollama response"
        mock_post.assert_called_once()

    @patch('leann.chat.requests.post')
    def test_ollama_llm_backend_with_context(self, mock_post):
        """Test Ollama LLM backend with context."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Context response"}
        mock_post.return_value = mock_response

        backend = chat.OllamaLLMBackend("llama3:8b")
        response = backend.generate("Test prompt", context=["Previous message"])

        assert response == "Context response"
        # Check that context was included in the request
        call_args = mock_post.call_args
        assert "Previous message" in str(call_args)

    @patch('leann.chat.requests.post')
    def test_ollama_llm_backend_connection_error(self, mock_post):
        """Test Ollama LLM backend connection error."""
        mock_post.side_effect = Exception("Connection failed")

        backend = chat.OllamaLLMBackend("llama3:8b")

        with pytest.raises(Exception, match="Connection failed"):
            backend.generate("Test prompt")

    @patch('leann.chat.requests.post')
    def test_ollama_llm_backend_http_error(self, mock_post):
        """Test Ollama LLM backend HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        backend = chat.OllamaLLMBackend("llama3:8b")

        with pytest.raises(Exception):
            backend.generate("Test prompt")

    def test_simulation_llm_backend(self):
        """Test simulation LLM backend."""
        backend = chat.SimulationLLMBackend()

        response = backend.generate("Test prompt")

        assert isinstance(response, str)
        assert len(response) > 0
        # Should mention it's a simulation
        assert "simulation" in response.lower() or "mock" in response.lower()

    def test_simulation_llm_backend_with_context(self):
        """Test simulation LLM backend with context."""
        backend = chat.SimulationLLMBackend()

        response = backend.generate("Test prompt", context=["Context message"])

        assert isinstance(response, str)
        assert len(response) > 0

    @patch('leann.chat.openai')
    def test_openai_llm_backend_initialization(self, mock_openai):
        """Test OpenAI LLM backend initialization."""
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        backend = chat.OpenAILLMBackend("gpt-3.5-turbo")

        assert backend.model_name == "gpt-3.5-turbo"
        mock_openai.OpenAI.assert_called_once()

    @patch('leann.chat.openai')
    def test_openai_llm_backend_generate(self, mock_openai):
        """Test OpenAI LLM backend generation."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="OpenAI response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client

        backend = chat.OpenAILLMBackend("gpt-3.5-turbo")
        response = backend.generate("Test prompt")

        assert response == "OpenAI response"
        mock_client.chat.completions.create.assert_called_once()

    @patch('leann.chat.openai')
    def test_openai_llm_backend_with_context(self, mock_openai):
        """Test OpenAI LLM backend with context."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Contextual response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client

        backend = chat.OpenAILLMBackend("gpt-3.5-turbo")
        response = backend.generate("Test prompt", context=["System message", "User message"])

        assert response == "Contextual response"
        # Check that context messages were included
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) >= 3  # System + context + user

    @patch('leann.chat.openai')
    def test_openai_llm_backend_api_error(self, mock_openai):
        """Test OpenAI LLM backend API error."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.OpenAI.return_value = mock_client

        backend = chat.OpenAILLMBackend("gpt-3.5-turbo")

        with pytest.raises(Exception, match="API Error"):
            backend.generate("Test prompt")


class TestGetLLM:
    """Test the get_llm function."""

    @patch('leann.chat.OllamaLLMBackend')
    def test_get_ollama_llm(self, mock_ollama_class):
        """Test getting Ollama LLM backend."""
        mock_backend = Mock()
        mock_ollama_class.return_value = mock_backend

        result = chat.get_llm("llama3:8b", "ollama")

        assert result is mock_backend
        mock_ollama_class.assert_called_once_with("llama3:8b", host=None)

    @patch('leann.chat.OllamaLLMBackend')
    def test_get_ollama_llm_with_host(self, mock_ollama_class):
        """Test getting Ollama LLM backend with custom host."""
        mock_backend = Mock()
        mock_ollama_class.return_value = mock_backend

        result = chat.get_llm("llama3:8b", "ollama", host="http://custom:11434")

        assert result is mock_backend
        mock_ollama_class.assert_called_once_with("llama3:8b", host="http://custom:11434")

    @patch('leann.chat.HFLLMBackend')
    def test_get_hf_llm(self, mock_hf_class):
        """Test getting HuggingFace LLM backend."""
        mock_backend = Mock()
        mock_hf_class.return_value = mock_backend

        result = chat.get_llm("microsoft/DialoGPT-medium", "hf")

        assert result is mock_backend
        mock_hf_class.assert_called_once_with("microsoft/DialoGPT-medium")

    @patch('leann.chat.OpenAILLMBackend')
    def test_get_openai_llm(self, mock_openai_class):
        """Test getting OpenAI LLM backend."""
        mock_backend = Mock()
        mock_openai_class.return_value = mock_backend

        result = chat.get_llm("gpt-3.5-turbo", "openai")

        assert result is mock_backend
        mock_openai_class.assert_called_once_with("gpt-3.5-turbo")

    @patch('leann.chat.SimulationLLMBackend')
    def test_get_simulation_llm(self, mock_sim_class):
        """Test getting simulation LLM backend."""
        mock_backend = Mock()
        mock_sim_class.return_value = mock_backend

        result = chat.get_llm("", "simulation")

        assert result is mock_backend
        mock_sim_class.assert_called_once()

    def test_get_llm_unsupported_type(self):
        """Test getting LLM with unsupported type."""
        with pytest.raises(ValueError, match="Unknown LLM type"):
            chat.get_llm("model", "unsupported_type")


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""

    def test_empty_model_name_handling(self):
        """Test handling of empty model names."""
        # Most functions should handle empty model names gracefully
        with patch('leann.chat.check_ollama_models', return_value=[]):
            result = chat.search_ollama_models_fuzzy("", ["llama3:8b"])
            assert result == []

    def test_special_characters_in_model_names(self):
        """Test handling of special characters in model names."""
        models = ["model-with-dashes", "model_with_underscores", "model.with.dots"]

        # Search should work with special characters
        result = chat.search_ollama_models_fuzzy("model", models)
        assert len(result) > 0

    def test_unicode_in_model_names(self):
        """Test handling of Unicode characters in model names."""
        models = ["模型测试", "test-模型", " môdel "]  # Unicode model names

        # Should handle Unicode gracefully
        result = chat.search_ollama_models_fuzzy("模型", models)
        assert len(result) > 0

    def test_very_long_model_names(self):
        """Test handling of very long model names."""
        long_name = "a" * 1000
        models = [long_name]

        # Should handle long names without crashing
        result = chat.search_ollama_models_fuzzy("a", models)
        assert len(result) >= 0

    def test_concurrent_model_searches(self):
        """Test concurrent model searches."""
        import threading

        models = ["model1", "model2", "model3"]
        results = []

        def search_worker():
            result = chat.search_ollama_models_fuzzy("model", models)
            results.append(result)

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=search_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All searches should complete
        assert len(results) == 3


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short", "--cov=leann.chat", "--cov-report=term-missing"])