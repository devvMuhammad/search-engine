"use client";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

// Add stem function above ResultCardProps
const getWordStem = (word: string): string => {
  const irregularPlurals: { [key: string]: string } = {
    children: "child",
    people: "person",
    mice: "mouse",
    leaves: "leaf",
    // Add more as needed
  };

  word = word.toLowerCase();

  if (irregularPlurals[word]) {
    return irregularPlurals[word];
  }

  if (word.endsWith("ies")) {
    return word.slice(0, -3) + "y";
  }

  if (word.endsWith("es")) {
    return word.slice(0, -2);
  }

  if (word.endsWith("s")) {
    return word.slice(0, -1);
  }

  return word;
};

interface ResultCardProps {
  query: string;
  result: {
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
}

// Modify highlightText function
const highlightText = (text: string, query: string) => {
  const queryStems = query.toLowerCase().split(" ").map(getWordStem);
  return text.split(" ").map((word, index) => {
    const wordStem = getWordStem(word);

    const isMatch = queryStems.some((stem) => wordStem.includes(stem));
    return isMatch ? (
      <>
        <mark key={index} className="bg-yellow-200">
          {word}
        </mark>{" "}
      </>
    ) : (
      word + " "
    );
  });
};

export default function ResultCard({ result, query }: ResultCardProps) {
  let keywordsArray;
  try {
    keywordsArray = JSON.parse(result.keywords.replace(/'/g, '"'));
  } catch (error) {
    keywordsArray = [JSON.stringify(result.keywords)];
    console.log(error);
  }

  let linksArray;
  try {
    // Handle array-like string of URLs
    if (result.url.startsWith("[") && result.url.endsWith("]")) {
      linksArray = JSON.parse(result.url.replace(/'/g, '"'));
    } else {
      // Handle single URL string
      linksArray = [result.url];
    }
  } catch (error) {
    linksArray = [result.url];
    console.log("URL parsing error:", error);
  }

  const validLinks = linksArray.filter(
    (link: string) =>
      link && link !== "None" && link !== "undefined" && link.startsWith("http")
  );
  const primaryLink = validLinks[0] || "#";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="w-full bg-white text-gray-800 border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-blue-600 hover:underline">
            <Link href={primaryLink} target="_blank">
              {highlightText(result.title, query)}
            </Link>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">
            {highlightText(result.abstract, query)}
          </p>
          <div className="flex flex-wrap gap-2 mb-4">
            {keywordsArray.map((keyword: string, index: number) => (
              <Badge
                key={index}
                variant="secondary"
                className="bg-gray-200 text-gray-700"
              >
                {highlightText(keyword.trim(), query)}
              </Badge>
            ))}
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-green-600">Year: {result.year}</span>
            <span className="text-orange-600">
              Citations: {result.citations}
            </span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
