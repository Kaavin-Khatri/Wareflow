import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { idToken } = body;

    if (!idToken || typeof idToken !== "string") {
      return NextResponse.json({ error: "Missing idToken" }, { status: 400 });
    }

    const cookieStore = await cookies();
    cookieStore.set("session", idToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 5, // 5 days
      path: "/",
    });

    return NextResponse.json({ status: "success" });
  } catch {
    return NextResponse.json({ error: "Failed to establish session" }, { status: 500 });
  }
}

export async function PATCH() {
  try {
    const cookieStore = await cookies();
    cookieStore.set("wareflow_2fa_verified", "true", {
      httpOnly: false,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 12, // 12 hours
      path: "/",
    });

    return NextResponse.json({ status: "2fa_verified" });
  } catch {
    return NextResponse.json({ error: "Failed to set 2fa verification" }, { status: 500 });
  }
}

export async function DELETE() {
  try {
    const cookieStore = await cookies();
    cookieStore.delete("session");
    cookieStore.delete("wareflow_2fa_verified");
    return NextResponse.json({ status: "logged_out" });
  } catch {
    return NextResponse.json({ error: "Failed to clear session" }, { status: 500 });
  }
}
