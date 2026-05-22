import { NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";
import type { PortfolioPosition } from "@/lib/portfolio";

export async function GET() {
  try {
    const { data } = await runPython<PortfolioPosition[]>("scripts.portfolio", {
      args: ["list"],
    });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      return NextResponse.json(
        { error: "Gagal membaca posisi", detail: err.stderr || err.stdout },
        { status: 500 },
      );
    }
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}

export async function POST(req: Request) {
  let positions: unknown;
  try {
    positions = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }

  try {
    const { data } = await runPython<{ saved: number }>("scripts.portfolio", {
      args: ["save", "--positions", JSON.stringify(positions)],
    });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      return NextResponse.json(
        { error: "Gagal menyimpan posisi", detail: err.stderr || err.stdout },
        { status: 422 },
      );
    }
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
