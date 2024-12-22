import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  query: string;
  setQuery: (query: string) => void;
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [input, setInput] = useState("");
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(input);
    // setQuery(input);
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        type="text"
        placeholder="Search for research papers..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="flex-grow text-gray-800"
      />
      <Button type="submit">Search</Button>
    </form>
  );
}
