import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";
import type { ImportResult } from "@/lib/portfolio";

export async function POST(req: NextRequest) {
  let body: { csv_content: string; field_map?: Record<string, string> };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }

  if (!body.csv_content || typeof body.csv_content !== "string") {
    return NextResponse.json({ error: "csv_content string required" }, { status: 400 });
  }

  const args = ["parse", "--csv-content", body.csv_content];
  if (body.field_map) {
    args.push("--field-map", JSON.stringify(body.field_map));
  }

  try {
    const { data } = await runPython<ImportResult>("scripts.portfolio", { args });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      return NextResponse.json(
        { error: "CSV import could not be parsed.", detail: "Check the CSV format and try again." },
        { status: 422 },
      );
    }
    return NextResponse.json({ error: "CSV import could not be parsed." }, { status: 500 });
  }
}
