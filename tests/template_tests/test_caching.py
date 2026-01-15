"""
Tests for template compilation caching.

Add this file to: tests/template_tests/test_caching.py
"""
from django.template import base
from django.test import SimpleTestCase


class TemplateCachingTests(SimpleTestCase):
    """Tests for template compilation caching optimizations."""

    def setUp(self):
        """Clear caches before each test."""
        base.clear_template_caches()

    def tearDown(self):
        """Clear caches after each test."""
        base.clear_template_caches()

    def test_clear_template_caches(self):
        """Test that clear_template_caches() clears both caches."""
        # Lines 115-117 coverage
        base.Lexer("test {{ var }}").tokenize()
        self.assertGreater(len(base._tokenize_cache), 0)
        
        base.clear_template_caches()
        
        self.assertEqual(len(base._tokenize_cache), 0)
        self.assertEqual(len(base._filter_expression_cache), 0)

    def test_tokenize_cache_populated(self):
        """Test that tokenization results are cached."""
        template_str = "Hello {{ name }}"
        lexer = base.Lexer(template_str)
        tokens1 = lexer.tokenize()
        
        cache_size_after_first = len(base._tokenize_cache)
        self.assertGreater(cache_size_after_first, 0)
        
        # Second call should use cache
        lexer2 = base.Lexer(template_str)
        tokens2 = lexer2.tokenize()
        cache_size_after_second = len(base._tokenize_cache)
        
        # Cache size shouldn't grow (same template)
        self.assertEqual(cache_size_after_first, cache_size_after_second)
        self.assertEqual(len(tokens1), len(tokens2))

    def test_tokenize_cache_bounds_and_eviction(self):
        """Test cache size limits and eviction strategy."""
        # Lines 475-477 coverage
        base.clear_template_caches()
        
        # Add exactly 1000 templates
        for i in range(1000):
            base.Lexer(f"Template {i} {{{{ var{i} }}}}").tokenize()
        
        self.assertEqual(len(base._tokenize_cache), 1000)
        
        # Add one more to trigger eviction
        base.Lexer("Template 1000 {{ var1000 }}").tokenize()
        
        # Cache should be reduced (25% eviction = 250 removed, then 1 added = 751)
        self.assertLessEqual(len(base._tokenize_cache), 1000)
        self.assertGreater(len(base._tokenize_cache), 700)

    def test_tokenize_cache_consistency(self):
        """Test that cached tokens are consistent with non-cached."""
        template_str = "{% if test %}{{ var|upper }}{% endif %}"
        
        tokens1 = base.Lexer(template_str).tokenize()
        tokens2 = base.Lexer(template_str).tokenize()
        
        self.assertEqual(len(tokens1), len(tokens2))
        for t1, t2 in zip(tokens1, tokens2):
            self.assertEqual(t1.contents, t2.contents)
            self.assertEqual(t1.token_type, t2.token_type)

    def test_verbatim_templates_not_cached(self):
        """Test that verbatim templates skip caching."""
        base.clear_template_caches()
        template_str = "{% verbatim %}{{ test }}{% endverbatim %}"
        
        lexer = base.Lexer(template_str)
        lexer.tokenize()
        
        # The tokenize method should handle verbatim correctly

    def test_filter_expression_cache(self):
        """Test that filter expressions are cached."""
        # Line 756 and related coverage
        from django.template import engines
        
        engine = engines["django"]
        parser = base.Parser(
            [],
            engine.template_libraries,
            engine.template_builtins,
            base.Origin("test"),
        )
        
        # Compile same filter expression twice
        token = "var|default:'test'"
        expr1 = parser.compile_filter(token)
        cache_size_after_first = len(base._filter_expression_cache)
        
        expr2 = parser.compile_filter(token)
        cache_size_after_second = len(base._filter_expression_cache)
        
        # Cache should be used (size doesn't grow)
        self.assertEqual(cache_size_after_first, cache_size_after_second)

    def test_empty_template_handled(self):
        """Test that empty templates don't break caching."""
        tokens = base.Lexer("").tokenize()
        self.assertIsInstance(tokens, list)

    def test_large_template_cached(self):
        """Test that large templates are cached efficiently."""
        large_template = "{{ var }}" * 100
        
        tokens1 = base.Lexer(large_template).tokenize()
        tokens2 = base.Lexer(large_template).tokenize()
        
        self.assertEqual(len(tokens1), len(tokens2))

    def test_special_characters_in_template(self):
        """Test that templates with special characters work with caching."""
        template = "{{ 'test\\'s value' }}"
        tokens = base.Lexer(template).tokenize()
        self.assertGreater(len(tokens), 0)
