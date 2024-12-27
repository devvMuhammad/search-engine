"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
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
import { toast } from "@/hooks/use-toast";

const documentSchema = z.object({
  abstract: z.string().min(1, "Abstract is required"),
  citations: z
    .number()
    .int()
    .nonnegative("Citations must be a non-negative integer"),
  doc_id: z.string().min(1, "Document ID is required"),
  keywords: z.array(z.string()).min(1, "At least one keyword is required"),
  score: z.number().min(0).max(100, "Score must be between 0 and 100"),
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

export function AddDocumentForm() {
  const form = useForm<DocumentFormValues>({
    resolver: zodResolver(documentSchema),
    defaultValues: {
      abstract: "",
      citations: 0,
      doc_id: "",
      keywords: [],
      score: 0,
      title: "",
      venue: "",
      year: new Date().getFullYear(),
      url: "",
    },
  });

  async function onSubmit(data: DocumentFormValues) {
    try {
      // TODO: Implement actual submission logic here
      console.log(data);
      toast({
        title: "Document added successfully",
        description: "The document has been added to the search engine.",
      });
      form.reset();
    } catch (error) {
      toast({
        title: "Error",
        description: "An error occurred while adding the document.",
        variant: "destructive",
      });
    }
  }

  return (
    <Form {...form}>
      <form
        id="add-document-form"
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-6"
      >
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
                <Textarea placeholder="Enter document abstract" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="doc_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Document ID</FormLabel>
              <FormControl>
                <Input placeholder="Enter document ID" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
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
        <FormField
          control={form.control}
          name="score"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Score</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  step="0.1"
                  {...field}
                  onChange={(e) => field.onChange(Number(e.target.value))}
                />
              </FormControl>
              <FormDescription>Enter a score between 0 and 100</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
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
        <FormField
          control={form.control}
          name="url"
          render={({ field }) => (
            <FormItem>
              <FormLabel>URL</FormLabel>
              <FormControl>
                <Input type="url" placeholder="Enter document URL" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </form>
    </Form>
  );
}
