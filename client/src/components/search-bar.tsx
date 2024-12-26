"use client";

import { useState, useEffect, useCallback, useRef, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import AutoSuggestions from "@/components/suggestions";
import { useDebounce } from "@/hooks/useDebounce";

interface SearchBarProps {
  onSearch: (query: string) => void;
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [hasSearched, setHasSearched] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const searchBarRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const fetchSuggestions = useCallback(async (input: string) => {
    setIsLoading(true);
    // Simulate API call
    const response = await fetch(
      `http://localhost:5000/autocomplete?q=${input}`
    );
    const data = await response.json();
    // console;
    setSuggestions(data.suggestions);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (debouncedQuery && !hasSearched) {
      fetchSuggestions(debouncedQuery);
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
    setSelectedIndex(-1);
  }, [debouncedQuery, fetchSuggestions, hasSearched]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchBarRef.current &&
        !searchBarRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
    setShowSuggestions(false);
    setHasSearched(true);
    inputRef.current?.blur(); // New line to blur the input after submission
  };

  const handleInputFocus = () => {
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (showSuggestions) {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < suggestions.length - 1 ? prev + 1 : prev
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        case "Enter":
          e.preventDefault();
          if (selectedIndex >= 0) {
            setQuery(suggestions[selectedIndex]);
            onSearch(suggestions[selectedIndex]);
            setShowSuggestions(false);
            setHasSearched(true);
            inputRef.current?.blur(); // New line to blur the input when selecting a suggestion with Enter
          } else {
            handleSubmit(e);
          }
          break;
        case "Escape":
          setShowSuggestions(false);
          break;
      }
    }
  };

  return (
    <div ref={searchBarRef}>
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex gap-2">
          <Input
            type="text"
            placeholder="Search for research papers..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setHasSearched(false);
            }}
            onFocus={handleInputFocus}
            onKeyDown={handleKeyDown}
            ref={inputRef}
            className="flex-grow text-gray-800"
          />
          <Button type="submit">Search</Button>
        </div>
        {showSuggestions && (isLoading || suggestions.length > 0) && (
          <AutoSuggestions
            suggestions={suggestions}
            isLoading={isLoading}
            selectedIndex={selectedIndex}
            onSelect={(suggestion) => {
              setQuery(suggestion);
              onSearch(suggestion);
              setShowSuggestions(false);
              setHasSearched(true);
              inputRef.current?.blur(); // New line to blur the input when selecting a suggestion
            }}
          />
        )}
      </form>
    </div>
  );
}
