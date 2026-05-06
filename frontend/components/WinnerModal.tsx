'use client';

interface WinnerModalProps {
  isOpen: boolean;
  cartelaNumber: number;
  winningCard: number[][];
  calledNumbers: number[];
  onClose: () => void;
}

export default function WinnerModal({
  isOpen,
  cartelaNumber,
  winningCard,
  calledNumbers,
  onClose,
}: WinnerModalProps) {
  if (!isOpen) return null;

  const getBingoLetter = (col: number) => {
    return ['B', 'I', 'N', 'G', 'O'][col];
  };

  const getNumberColor = (num: number) => {
    if (num >= 1 && num <= 15) return 'bg-blue-500';
    if (num >= 16 && num <= 30) return 'bg-indigo-500';
    if (num >= 31 && num <= 45) return 'bg-purple-500';
    if (num >= 46 && num <= 60) return 'bg-green-500';
    if (num >= 61 && num <= 75) return 'bg-orange-500';
    return 'bg-gray-500';
  };

  const isNumberCalled = (num: number) => {
    return calledNumbers.includes(num);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-3xl p-8 max-w-2xl w-full border-2 border-yellow-500/50 shadow-2xl">
        {/* Crown Icon */}
        <div className="flex justify-center mb-4">
          <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-xl">
            <span className="text-5xl">👑</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-center text-5xl font-black text-yellow-400 mb-2">
          BINGO!
        </h1>
        <p className="text-center text-2xl text-white mb-6">
          🎉 bi WON! 🎉
        </p>

        {/* Cartela Number */}
        <div className="bg-gray-700/50 rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-center gap-2 mb-4">
            <span className="text-yellow-400 text-2xl">🏆</span>
            <h2 className="text-white text-xl font-bold">
              Winning Cartela : {cartelaNumber}
            </h2>
          </div>

          {/* BINGO Header */}
          <div className="grid grid-cols-5 gap-2 mb-2">
            {['B', 'I', 'N', 'G', 'O'].map((letter, idx) => (
              <div
                key={letter}
                className={`${getNumberColor((idx * 15) + 1)} text-white font-bold text-center py-3 rounded-xl shadow-lg`}
              >
                {letter}
              </div>
            ))}
          </div>

          {/* Winning Card */}
          <div className="grid grid-cols-5 gap-2">
            {winningCard.map((column, colIdx) =>
              column.map((num, rowIdx) => (
                <div
                  key={`${colIdx}-${rowIdx}`}
                  className={`aspect-square rounded-xl font-bold text-xl flex items-center justify-center shadow-md transition-all ${
                    num === 0
                      ? 'bg-yellow-500 text-gray-900'
                      : isNumberCalled(num)
                      ? 'bg-green-500 text-white ring-2 ring-green-300'
                      : 'bg-white text-gray-800'
                  }`}
                >
                  {num === 0 ? '✨' : num}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Auto-starting message */}
        <div className="bg-gray-700/30 rounded-xl p-4 text-center mb-6">
          <p className="text-white/80 flex items-center justify-center gap-2">
            <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></span>
            Auto-starting next game in 5s
          </p>
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-bold py-4 rounded-xl transition-all shadow-lg"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
