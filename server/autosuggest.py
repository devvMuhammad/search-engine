from server.entities.lexicon import Lexicon

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.frequency = 0  # Can be used to rank suggestions

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        """Insert a word into the trie."""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.frequency += 1
    
    def _find_prefix_node(self, prefix):
        """Helper function to find the node corresponding to a prefix."""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node
    
    def _collect_suggestions(self, node, prefix, suggestions, max_suggestions=5):
        """Recursively collect word suggestions starting from a node."""
        if len(suggestions) >= max_suggestions:
            return
        
        if node.is_end_of_word:
            suggestions.append(prefix)
            
        for char, child_node in sorted(node.children.items()):
            self._collect_suggestions(child_node, prefix + char, suggestions, max_suggestions)
    
    def get_suggestions(self, prefix, max_suggestions=5):
        """Get autocomplete suggestions for a given prefix."""
        node = self._find_prefix_node(prefix)
        if not node:
            return []
            
        suggestions = []
        self._collect_suggestions(node, prefix, suggestions, max_suggestions)
        return suggestions

class Autosuggestion:
    def __init__(self, word_list):
        """Initialize autosuggestion with a list of words."""
        self.trie = Trie()
        for word in word_list:
            self.trie.insert(word.lower())
    
    def suggest(self, prefix, max_suggestions=5):
        """Get suggestions for a given prefix."""
        return self.trie.get_suggestions(prefix.lower(), max_suggestions)

# Example usage
def main():
    # Sample lexicon
    
    words_list = list(Lexicon().lexicon.keys())
    
    # Initialize autosuggestion
    auto = Autosuggestion(words_list)
    
    # Test cases
    while True:
        prefix = input("Enter a prefix: ")
        if not prefix:
            break
        suggestions = auto.suggest(prefix)
        print(suggestions)

if __name__ == "__main__":
    main()