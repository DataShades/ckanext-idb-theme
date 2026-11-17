/*
 * Renders the AI dataset suggestions from the rendered cards and score map.
 *
 * The server renders only an empty slot; the semantic lookup is requested here
 * so it never delays the search results. Matching Solr results get a similarity
 * badge, and the AI-only cards are moved above or into the results.
 *
 * endpoint - URL of the semantic suggestions view, with the query and shown ids
 * q        - search query of the first results page
 * timeout  - client deadline in ms
 */
ckan.module("idb-ai-suggestions", function ($) {
  "use strict";

  return {
    options: {
      endpoint: null,
      q: "",
      timeout: 10000,
    },

    initialize: function () {
      if (!this.options.endpoint) {
        return;
      }

      var self = this;
      var controller = new AbortController();
      var timer = setTimeout(function () {
        controller.abort();
      }, this.options.timeout);

      fetch(this.options.endpoint, { signal: controller.signal, credentials: "same-origin" })
        .then(function (response) {
          return response.text();
        })
        .then(function (html) {
          self._render(html);
        })
        .catch(function () {
          // a failed or timed out request leaves the slot empty
        })
        .finally(function () {
          clearTimeout(timer);
        });
    },

    _render: function (html) {
      var self = this;
      var doc = new DOMParser().parseFromString(html, "text/html");
      var script = doc.querySelector("script[data-ka-ai-scores]");
      if (!script) {
        return;
      }

      var scores;
      try {
        scores = JSON.parse(script.textContent);
      } catch (error) {
        return;
      }

      this.el.empty();

      var high = $(doc).find(".idb-ai-suggestions__high > li");
      var low = $(doc).find(".idb-ai-suggestions__low > li");
      var cards = high.toArray().concat(low.toArray());
      var solrItems = $(".dataset-item");

      cards.forEach(function (card) {
        var id = $(card).find(".ka-result-marker").attr("data-ka-dataset-id");
        if (scores.cards[id] === undefined) {
          return;
        }
        self._setCardBadge($(card), scores.cards[id]);
      });

      Object.keys(scores.solr || {}).forEach(function (id) {
        var $heading = $(".ka-result-marker")
          .filter(function () {
            return $(this).attr("data-ka-dataset-id") === id;
          })
          .first()
          .closest(".dataset-heading");
        if (!$heading.length || $heading.find(".idb-ai-suggestions__badge").length) {
          return;
        }
        $heading.append(self._badge(scores.solr[id]));
      });

      if (!solrItems.length) {
        if (cards.length) {
          $(".search-results-count").text(this._("No exact matches, you might be looking for"));
          $(".search-empty").prop("hidden", true);
          this.el.append(this._list(cards));
        }
        return;
      }

      if (this._strong(solrItems)) {
        if (cards.length) {
          this._inline(cards, solrItems);
        }
        return;
      }

      var above = high.toArray().slice(0, 3);
      var rest = high.toArray().slice(3).concat(low.toArray());
      if (above.length) {
        this.el.append(this._aboveBlock(this._("AI suggestions"), above));
      }
      if (rest.length) {
        this._inline(rest, solrItems);
      }
    },

    _setCardBadge: function ($card, pct) {
      var $badge = $card.find(".ka-similarity-badge").first();
      if (!$badge.length) {
        return;
      }
      $badge.contents().filter(function () {
        return this.nodeType === 3;
      }).remove();
      $badge.append(" " + this._("AI suggestion")).attr("title", this._score(pct));
    },

    _badge: function (pct) {
      return $("<span>", {
        class: "badge bg-info ms-2 idb-ai-suggestions__badge",
        title: this._score(pct),
      })
        .append($("<i>", { class: "fa fa-brain", "aria-hidden": "true" }))
        .append(" " + this._("AI match"));
    },

    _score: function (pct) {
      return this._("AI similarity %(score)s", { score: pct + "%" });
    },

    _aboveBlock: function (heading, cards) {
      var $section = $("<section>", {
        class: "idb-ai-suggestions__block mb-3",
        "aria-label": heading,
      });
      $section.append($("<h2>", { class: "h5 mb-2" }).text(heading));
      $section.append(this._list(cards));
      return $section;
    },

    _list: function (cards) {
      var $list = $("<ul>", { class: "dataset-list list-unstyled d-flex flex-column gap-3 w-100" });
      cards.forEach(function (card) {
        $list.append(card);
      });
      return $list;
    },

    _inline: function (cards, $solrItems) {
      var index = Math.min(3, $solrItems.length) - 1;
      if (index < 0) {
        return;
      }

      var target = "idb-ai-suggestions-inline";
      var $row = $("<li>", { class: "idb-ai-suggestions__inline" });
      var $button = $("<button>", {
        type: "button",
        class: "btn btn-link p-0",
        "data-bs-toggle": "collapse",
        "data-bs-target": "#" + target,
        "aria-expanded": "false",
        "aria-controls": target,
      }).text(this._("AI suggestions (%(count)s)", { count: cards.length }));

      var $collapse = $("<div>", { class: "collapse", id: target }).append(this._list(cards));
      $row.append($button).append($collapse);
      $solrItems.eq(index).after($row);
    },

    _strong: function ($solrItems) {
      var self = this;
      var q = this._normalize(this.options.q);
      var titles = $solrItems
        .find(".dataset-heading a")
        .map(function () {
          return $(this).text();
        })
        .get();

      if (
        titles.some(function (title) {
          return self._normalize(title) === q;
        })
      ) {
        return true;
      }

      var first = this._normalize(titles[0] || "");
      var words = this._tokens(q);
      return words.length > 1 && words.every(function (word) {
        return first.indexOf(word) !== -1;
      });
    },

    _tokens: function (text) {
      return this._normalize(text).split(" ").filter(Boolean);
    },

    _normalize: function (text) {
      return (text || "").replace(/\s+/g, " ").trim().toLowerCase();
    },
  };
});
