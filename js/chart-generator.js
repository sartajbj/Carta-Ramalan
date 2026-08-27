"use strict";

/*
 * CartaLotto Daily Chart Generator
 * Generates the same deterministic 4x4 matrix
 * from the selected date.
 */

function cartaLottoSeededRandom(seed) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generateDailyMatrix(date, offset = 0) {
  const seed =
    date.getDate() *
    (date.getMonth() + 1) *
    date.getFullYear() +
    offset;

  const nums = [];

  for (let i = 0; i < 4; i++) {
    nums.push(
      Math.floor(cartaLottoSeededRandom(seed + i) * 10)
    );
  }

  nums.push(
    nums[3],
    nums[2],
    Math.floor(cartaLottoSeededRandom(seed + 10) * 10),
    Math.floor(cartaLottoSeededRandom(seed + 11) * 10)
  );

  nums.push(
    nums[7],
    nums[6],
    Math.floor(cartaLottoSeededRandom(seed + 20) * 10),
    Math.floor(cartaLottoSeededRandom(seed + 21) * 10)
  );

  nums.push(
    nums[11],
    nums[10],
    Math.floor(cartaLottoSeededRandom(seed + 30) * 10),
    Math.floor(cartaLottoSeededRandom(seed + 31) * 10)
  );

  return nums;
}

function getCartaLottoChartPath(index) {
  const paths = [
    [5, 6, 10, 14],
    [1, 5, 10, 15],
    [0, 4, 8, 12],
    [3, 6, 9, 12]
  ];

  return paths[index % paths.length];
}

function isMTPDay(date) {
  const day = date.getDay();

  // Sunday = 0
  // Wednesday = 3
  // Saturday = 6

  return [0, 3, 6].includes(day);
}

function getChartType(date) {
  return isMTPDay(date) ? "mtp" : "gdl";
}

function getChartTitle(date, type) {
  const formatted = date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric"
  });

  if (type === "mtp") {
    return `Ramalan 4D MTP and SGP Chart For ${formatted}`;
  }

  return `GDL Perdana Forecast Chart For ${formatted}`;
}
