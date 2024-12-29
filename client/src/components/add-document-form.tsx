"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";
import { useState } from "react";
// import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { CardContent, CardFooter } from "./ui/card";
import { Button } from "./ui/button";

const documentSchema = z.object({
  abstract: z.string().min(1, "Abstract is required"),
  citations: z
    .number()
    .int()
    .nonnegative("Citations must be a non-negative integer"),
  keywords: z.array(z.string()).min(1, "At least one keyword is required"),
  title: z.string().min(1, "Title is required"),
  venue: z.string().min(1, "Venue is required"),
  year: z
    .number()
    .int()
    .min(1900)
    .max(
      new Date().getFullYear(),
      "Year must be between 1900 and current year"
    ),
  url: z.string().url("Must be a valid URL"),
});

type DocumentFormValues = z.infer<typeof documentSchema>;

function FileUploadZone({
  onFileAccepted,
}: {
  onFileAccepted: (data: DocumentFormValues) => void;
}) {
  const { toast } = useToast();
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "application/json": [".json"],
    },
    multiple: false,
    onDrop: async (acceptedFiles) => {
      const file = acceptedFiles[0];
      console.log(file);
      if (!file) return;

      try {
        const text = await file.text();
        console.log(text);
        const json = JSON.parse(text);

        // Validate with zod schema
        const result = documentSchema.safeParse({
          title: json.title,
          abstract: json.abstract,
          keywords: json.keywords,
          year: Number(json.year),
          citations: Number(json.citations),
          url: json.url,
          venue: json.venue.raw,
        });

        console.log(result);

        if (!result.success) {
          toast({
            title: "Invalid JSON format",
            description: "The uploaded file doesn't match the required schema.",
            variant: "destructive",
          });
          return;
        }

        onFileAccepted({
          title: result.data.title,
          abstract: result.data.abstract,
          keywords: result.data.keywords,
          year: Number(result.data.year),
          citations: Number(result.data.citations),
          url: result.data.url,
          venue: result.data.venue,
        });
      } catch (error) {
        console.log(error);
        toast({
          title: "Error parsing JSON",
          description: "Please ensure the file contains valid JSON data.",
          variant: "destructive",
        });
      }
    },
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
        isDragActive ? "border-primary bg-primary/5" : "border-gray-300"
      )}
    >
      <input {...getInputProps()} />
      <div className="text-sm text-gray-600">
        <p>Drag and drop a JSON document file here, or click to select</p>
        <p className="text-xs mt-2">Supported format: .json</p>
      </div>
    </div>
  );
}

function transformToBackendFormat(formData: DocumentFormValues) {
  console.log(formData);
  return {
    title: formData.title,
    keywords: formData.keywords,
    venue: {
      raw: formData.venue,
    },
    year: formData.year,
    n_citation: formData.citations,
    url: [formData.url],
    abstract: formData.abstract,
    authors: [],
    doc_type: "Paper",
    references: [],
  };
}

export function AddDocumentForm() {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const form = useForm<DocumentFormValues>({
    resolver: zodResolver(documentSchema),
    defaultValues: {
      abstract: "",
      citations: 0,
      keywords: [],
      title: "",
      venue: "",
      year: new Date().getFullYear(),
      url: "",
    },
  });

  const handleFileAccepted = (data: DocumentFormValues) => {
    form.reset(data);
    toast({
      title: "File uploaded successfully",
      description: "Form fields have been populated with the file data.",
    });
  };

  async function onSubmit(data: DocumentFormValues) {
    setIsSubmitting(true);
    try {
      console.log(transformToBackendFormat(data));
      const response = await fetch("http://localhost:4000/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(transformToBackendFormat(data)),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      toast({
        title: "Document added successfully",
        description: "The document has been added to the search engine.",
      });
      form.reset();
    } catch (err) {
      console.error(err);
      toast({
        title: "Error",
        description: "An error occurred while adding the document.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <CardContent>
        <Form {...form}>
          <form
            id="add-document-form"
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-6"
          >
            <FileUploadZone onFileAccepted={handleFileAccepted} />
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter document title" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="abstract"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Abstract</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter document abstract"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-x-16">
              <FormField
                control={form.control}
                name="keywords"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Keywords</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter keywords separated by commas"
                        {...field}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value.split(",").map((k) => k.trim())
                          )
                        }
                      />
                    </FormControl>
                    <FormDescription>
                      Enter keywords separated by commas
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="citations"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Citations</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-x-16">
              <FormField
                control={form.control}
                name="venue"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Venue</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter publication venue" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="year"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Year</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>URL</FormLabel>
                  <FormControl>
                    <Input
                      type="url"
                      placeholder="Enter document URL"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>
      </CardContent>
      <CardFooter className="flex justify-end">
        <Button disabled={isSubmitting} type="submit" form="add-document-form">
          Add Document
        </Button>
      </CardFooter>
    </>
  );
}
