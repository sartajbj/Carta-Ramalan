"use strict";

/*
 * CartaLotto Daily Feed
 * ----------------------
 * Every day:
 *   GDL Perdana
 *
 * Wednesday / Saturday / Sunday:
 *   GDL Perdana
 *   Ramalan 4D MTP & SGP
 *
 * Newest date appears first.
 */

(function () {

  const feed = document.getElementById("feed");

  if (!feed) return;

  function formatUK(date) {
    return date.toLocaleDateString("en-GB");
  }

  function formatLong(date) {
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric"
    });
  }

  function formatShort(date) {
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "2-digit",
      year: "numeric"
    }).replace(/,/g, "");
  }

  function isMTPDay(date) {
    return [0, 3, 6].includes(date.getDay());
  }

  function getPostIntro(type, date) {

    const dateText = formatLong(date);

    if (type === "mtp") {
      return `
        Today's Ramalan 4D MTP and SGP chart for ${dateText}
        provides the latest free Carta Lotto forecast information.
        Review the complete 4×4 chart and use the information only
        as a reference when making your own decision.
      `;
    }

    return `
      Today's GDL Perdana forecast chart for ${dateText}
      provides the latest Carta Lotto chart information.
      Check the complete 4×4 matrix and compare the date carefully
      with previous daily updates.
    `;
  }

  function createCells(numbers, activePath) {

    return numbers.map(function (number, index) {

      const active = activePath.includes(index)
        ? " active"
        : "";

      return `
        <div class="cell${active}">
          ${number}
        </div>
      `;

    }).join("");
  }

  function createPost(date, type, index) {

    const isMTP = type === "mtp";

    const numbers = generateDailyMatrix(date, index);

    const activePath =
      getCartaLottoChartPath(index);

    const title =
      getChartTitle(date, type);

    const intro =
      getPostIntro(type, date);

    return `
      <article class="post-card">

        <div class="post-content">

          <div class="post-meta">

            <span class="badge ${isMTP ? "mtp" : "gdl"}">
              ${isMTP ? "MTP + SGP" : "GDL PERDANA"}
            </span>

            <span>
              Chart Update: ${formatShort(date)}
            </span>

          </div>

          <h2>
            ${title}
          </h2>

          <p class="post-intro">
            ${intro}
          </p>

          <div class="chart-shell">

            <div class="chart ${isMTP ? "mtp" : ""}">

              <div class="chart-heading">
                ${
                  isMTP
                    ? "RAMALAN 4D MTP & SGP"
                    : "CARTA RAMALAN GDL PERDANA"
                }
              </div>

              <div class="chart-date">
                ${formatUK(date)}
              </div>

              <div class="matrix">
                ${createCells(numbers, activePath)}
              </div>

              <div class="watermark">
                CARTALOTTO.COM
              </div>

            </div>

          </div>

          <div class="post-footer">

            <span>
              Free forecast information
            </span>

            <span>
              ${formatLong(date)}
            </span>

          </div>

        </div>

      </article>
    `;
  }

  function renderDailyFeed() {

    let html = "";

    /*
     * Last 7 calendar days.
     * i = 0 means TODAY.
     */

    for (let i = 0; i < 7; i++) {

      const date = new Date();

      date.setHours(12, 0, 0, 0);

      date.setDate(
        date.getDate() - i
      );

      /*
       * GDL is published every day.
       */
      html += createPost(
        date,
        "gdl",
        i
      );

      /*
       * MTP + SGP:
       * Sunday = 0
       * Wednesday = 3
       * Saturday = 6
       */
      if (isMTPDay(date)) {

        html += createPost(
          date,
          "mtp",
          i + 20
        );

      }

    }

    feed.innerHTML = html;
  }

  renderDailyFeed();

})();
