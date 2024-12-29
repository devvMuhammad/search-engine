"use client";

import { useState, useCallback, useMemo, useTransition } from "react";
import SearchBar from "@/components/search-bar";
import ResultCard from "@/components/result-card";
import SkeletonCard from "@/components/skeleton-card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

type ResultType = {
  abstract: string;
  n_citation: string;
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
  const [sortBy, setSortBy] = useState<"year" | "citations" | "def">("def");
  const [isPending, startTransition] = useTransition();

  const handleSearch = useCallback(async (query: string) => {
    setFirstRender(false);
    setIsLoading(true);
    setResults([]);
    const start = new Date().getTime();

    fetch(`http://localhost:4000/search?q=${query}`)
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

  const sortedResults = useMemo(() => {
    if (sortBy === "def") return results;

    return [...results].sort((a, b) => {
      if (!a || !b) {
        return 0;
      }
      if (sortBy === "year") {
        return parseInt(b.year) - parseInt(a.year);
      }
      return parseInt(b.n_citation) - parseInt(a.n_citation);
    });
  }, [results, sortBy]);

  return (
    <main className="min-h-screen">
      <div className="container mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold text-center mb-8">Info Hunt</h1>
        <SearchBar onSearch={handleSearch} />
        <div className="mt-8">
          <div className="flex justify-between items-center mb-4">
            {!isLoading && searchTime > 0 && (
              <p className="text-sm text-gray-600">
                Search completed in {searchTime}ms
              </p>
            )}

            {results.length > 0 && (
              <Select
                value={sortBy}
                onValueChange={(val) => {
                  startTransition(() => {
                    setSortBy(val as "def" | "year" | "citations");
                  });
                }}
              >
                <SelectTrigger className="w-[180px]">
                  <div className="flex items-center gap-2">
                    <SelectValue placeholder="Sort by..." />
                    {isPending && (
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-500 border-t-transparent" />
                    )}
                  </div>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="def">Default</SelectItem>
                  <SelectItem value="year">Year</SelectItem>
                  <SelectItem value="citations">Citations</SelectItem>
                </SelectContent>
              </Select>
            )}
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[...Array(6)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {sortedResults.length > 0
                ? sortedResults.map((result, i) => (
                    <div
                      key={i}
                      className={cn(
                        isPending && "opacity-50 transition-opacity"
                      )}
                    >
                      <ResultCard result={result} query={query} />
                    </div>
                  ))
                : !firstRender && (
                    <p className="text-xl text-center text-gray-600 mt-8">
                      No results found
                    </p>
                  )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
