import { motion } from "framer-motion";

interface AutoSuggestionsProps {
  suggestions: string[];
  isLoading: boolean;
  selectedIndex: number;
  onSelect: (suggestion: string) => void;
}

export default function AutoSuggestions({
  suggestions,
  isLoading,
  selectedIndex,
  onSelect,
}: AutoSuggestionsProps) {
  return (
    <motion.div
      className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      {isLoading ? (
        <div className="p-2 space-y-2">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="h-6 bg-gray-200 rounded animate-pulse"
            ></div>
          ))}
        </div>
      ) : (
        <ul className="py-1">
          {suggestions.map((suggestion, index) => (
            <li
              key={index}
              className={`px-4 py-2 cursor-pointer text-gray-800 ${
                index === selectedIndex ? "bg-blue-100" : "hover:bg-gray-100"
              }`}
              onClick={() => onSelect(suggestion)}
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </motion.div>
  );
}
