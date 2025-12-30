import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const allowedDomain = process.env.ALLOWED_EMAIL_DOMAIN || "seh.foundation";

const nextAuth = NextAuth.default ?? NextAuth;
const googleProvider = GoogleProvider.default ?? GoogleProvider;

const handler = nextAuth({
  providers: [
    googleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      authorization: { params: { prompt: "select_account" } },
    }),
  ],
  callbacks: {
    async signIn({ profile }) {
      const email = profile?.email || "";
      return email.endsWith(`@${allowedDomain}`);
    },
  },
  session: { strategy: "jwt" },
});

export { handler as GET, handler as POST };
