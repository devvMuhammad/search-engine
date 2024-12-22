import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function SkeletonCard() {
  return (
    <Card className="w-full bg-white text-gray-800 border-gray-200 shadow-sm">
      <CardHeader>
        <div className="h-6 bg-gray-200 rounded w-3/4 animate-pulse"></div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 mb-4">
          <div className="h-4 bg-gray-200 rounded w-full animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-4/6 animate-pulse"></div>
        </div>
        <div className="flex flex-wrap gap-2 mb-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="h-6 w-16 bg-gray-200 rounded animate-pulse"
            ></div>
          ))}
        </div>
        <div className="flex justify-between">
          <div className="h-4 bg-gray-200 rounded w-1/4 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4 animate-pulse"></div>
        </div>
      </CardContent>
    </Card>
  );
}
