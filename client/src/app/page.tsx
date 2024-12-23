"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import SearchBar from "@/components/search-bar";
import ResultCard from "@/components/result-card";
import SkeletonCard from "@/components/skeleton-card";

type ResultType = {
  abstract: string;
  citations: string;
  doc_id: string;
  keywords: string;
  score: number;
  title: string;
  venue: string;
  year: string;
  url: string;
};

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [firstRender, setFirstRender] = useState(true);
  const [results, setResults] = useState<ResultType[]>([]);
  const [searchTime, setSearchTime] = useState(0);

  const handleSearch = useCallback(async (query: string) => {
    setFirstRender(false);
    setIsLoading(true);
    setResults([]);
    const start = new Date().getTime();

    fetch(`http://127.0.0.1:5000/search?q=${query}`)
      .then((res) => res.json())
      .then((data) => {
        setIsLoading(false);
        console.log(data.results);
        setResults(data.results);
        setQuery(data.query);
        const end = new Date().getTime();
        setSearchTime(end - start);
      });
  }, []);

  return (
    <main className="min-h-screen bg-gray-100 text-gray-800">
      <div className="container mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold text-center mb-8">
          Research Search Engine
        </h1>
        <SearchBar query={query} setQuery={setQuery} onSearch={handleSearch} />
        <div className="mt-8">
          {!isLoading && searchTime > 0 && (
            <p className="text-sm text-gray-600 mb-4">
              Search completed in {searchTime}ms
            </p>
          )}
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(6)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <motion.div
              className="space-y-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              {results.length > 0
                ? results.map((result, i) => (
                    <ResultCard key={i} result={result} query={query} />
                  ))
                : !firstRender && (
                    <p className="text-xl text-center text-gray-600 mt-8">
                      No results found
                    </p>
                  )}
            </motion.div>
          )}
        </div>
      </div>
    </main>
  );
}
