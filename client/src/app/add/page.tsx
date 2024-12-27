"use client";

import { AddDocumentForm } from "@/components/add-document-form";
import { DockDemo } from "@/components/dock";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function AddDocumentPage() {
  return (
    <div className="container mx-auto py-10">
      <div className="flex items-center justify-center mb-6">
        <Link href="http://localhost:3000/">
          <ArrowLeft
            className="w-8 h-8 mr-2 cursor-pointer"
            onClick={() => window.history.back()}
          />
        </Link>
        <h1 className="text-4xl font-bold text-center">
          Add Document to Search Engine
        </h1>
      </div>
      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle>Document Details</CardTitle>
          <CardDescription>
            Enter the details of the document you want to add to the search
            engine.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AddDocumentForm />
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button type="submit" form="add-document-form">
            Add Document
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
