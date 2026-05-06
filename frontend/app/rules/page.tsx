'use client';

import { useRouter } from 'next/navigation';

export default function RulesPage() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-white/80 hover:text-white"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span>Back</span>
        </button>
        <h1 className="text-white font-bold text-xl">ጨዋታ ህጎች</h1>
        <div className="w-16"></div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Progress Indicator */}
        <div className="flex items-center justify-between text-sm text-white/60 mb-6">
          <span>1 of 4</span>
          <div className="flex-1 mx-4 h-1 bg-white/20 rounded-full overflow-hidden">
            <div className="h-full w-1/4 bg-purple-500 rounded-full"></div>
          </div>
          <span>መጀመሪያ</span>
        </div>

        {/* Tabs */}
        <div className="grid grid-cols-4 gap-2 mb-6">
          <button className="bg-white/10 text-white py-2 px-3 rounded-lg text-sm">
            መጀመሪያ
          </button>
          <button className="bg-white/5 text-white/60 py-2 px-3 rounded-lg text-sm">
            ጨዋታ
          </button>
          <button className="bg-white/5 text-white/60 py-2 px-3 rounded-lg text-sm">
            አሸናፊ
          </button>
          <button className="bg-white/5 text-white/60 py-2 px-3 rounded-lg text-sm">
            ክፍያ
          </button>
        </div>

        {/* Rule Card */}
        <div className="bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-2xl p-6 border border-cyan-500/30">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-cyan-500 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"/>
              </svg>
            </div>
            <h2 className="text-white text-xl font-bold">መጀመሪያ ካርድ</h2>
          </div>
          <p className="text-white/80 leading-relaxed">
            ጨዋታውን ለመጀመር እንደምትፈልጉት ገንዘብ መጠን ይምረጡ። ከዚያ ከ1-600 የካርድ ቁጥሮች ውስጥ አንድ ካርድ ይምረጡ። የመመዝገቢያ ጊዜው ከመጠናቀቁ በፊት ካርድዎን ያረጋግጡ።
          </p>
        </div>

        <div className="bg-gradient-to-br from-red-500/20 to-pink-500/20 rounded-2xl p-6 border border-red-500/30">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              2
            </div>
            <h2 className="text-white text-xl font-bold">የካርድ ሁኔታ አመላካች</h2>
          </div>
          <p className="text-white/80 leading-relaxed">
            የመጀመሪያ ካርድ ሐምራዊ ነው። የተመረጠ ካርድ አረንጓዴ ይሆናል። በሌሎች ተጫዋቾች የተመረጠ ካርድ ቀይ ይሆናል። ቀይ ካርዶችን መምረጥ አይችሉም።
          </p>
        </div>

        <div className="bg-gradient-to-br from-blue-500/20 to-indigo-500/20 rounded-2xl p-6 border border-blue-500/30">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              3
            </div>
            <h2 className="text-white text-xl font-bold">የካርድ ቅድመ እይታ</h2>
          </div>
          <p className="text-white/80 leading-relaxed">
            የመጀመሪያ ካርድ ሲመርጡ ካርዱን ማየት ይችላሉ። ካርዱ ከመጀመሪያ ካርድ ጋር የሚመሳሰል ከሆነ መጀመሪያ ካርድን ያረጋግጡ።
          </p>
        </div>

        <div className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 rounded-2xl p-6 border border-yellow-500/30">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-gray-900" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
              </svg>
            </div>
            <h2 className="text-white text-xl font-bold">የካርድ ምርጫ ጠቃሚ ምክሮች</h2>
          </div>
          <ul className="space-y-2 text-white/80">
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-1">✓</span>
              <span>በቀይ ያልተመለከቱ ካርዶችን ይምረጡ</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-1">✓</span>
              <span>ካርድዎን ከማረጋገጥዎ በፊት ይመልከቱ</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-1">✓</span>
              <span>የመመዝገቢያ ጊዜ ከመጠናቀቁ በፊት በፍጥነት ይምረጡ</span>
            </li>
          </ul>
        </div>

        <div className="bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-2xl p-6 border border-indigo-500/30">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-indigo-500 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/>
              </svg>
            </div>
            <h2 className="text-white text-xl font-bold">የመመዝገቢያ ጊዜ</h2>
          </div>
          <p className="text-white/80 leading-relaxed">
            ወደ ጨዋታው ለመቀላቀል የ1 ደቂቃ ጊዜ አለዎት። ጊዜው ካለቀ በኋላ ካርድዎ ይቆለፋል እና ጨዋታው ይጀምራል። ስለዚህ በፍጥነት ይምረጡ።
          </p>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-white/10">
        <div className="grid grid-cols-4 gap-1 p-2">
          <button
            onClick={() => router.push('/')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 3.5L2 9.5v8h5v-5h6v5h5v-8l-8-6z"/>
            </svg>
            <span className="text-xs">Game</span>
          </button>
          
          <button
            onClick={() => router.push('/history')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9V7h2v6z"/>
            </svg>
            <span className="text-xs">History</span>
          </button>
          
          <button
            onClick={() => router.push('/wallet')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z"/>
            </svg>
            <span className="text-xs">Wallet</span>
          </button>
          
          <button
            onClick={() => router.push('/profile')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a4 4 0 100 8 4 4 0 000-8zm0 10c-4.42 0-8 1.79-8 4v2h16v-2c0-2.21-3.58-4-8-4z"/>
            </svg>
            <span className="text-xs">Profile</span>
          </button>
        </div>
      </div>
    </main>
  );
}
