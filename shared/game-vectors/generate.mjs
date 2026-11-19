// Regenerates the golden vectors in this folder.
//
// ORACLE: wherever possible the expected values come from the *actual* prototype
// code in animon-web/src/lib/{data,game}.ts (read-only reference, never edited).
// The two files are copied to a temp dir (only to add ".ts" import extensions)
// and imported with Node's built-in TypeScript stripping (Node >= 22.6).
//
// Cases where the product deliberately differs from the prototype are written
// by hand and marked "(R8)" or "(R18)": see specs/001-mobile-core-loop/research.md.
//
// Usage (from the repo root):  node shared/game-vectors/generate.mjs

import { mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const protoLib = join(here, "..", "..", "animon-web", "src", "lib");
const tmp = mkdtempSync(join(tmpdir(), "animon-oracle-"));
try {
  writeFileSync(join(tmp, "data.ts"), readFileSync(join(protoLib, "data.ts"), "utf8"));
  writeFileSync(
    join(tmp, "game.ts"),
    readFileSync(join(protoLib, "game.ts"), "utf8").replace(/from "\.\/data"/g, 'from "./data.ts"'),
  );
  const data = await import(pathToFileURL(join(tmp, "data.ts")).href);
  const game = await import(pathToFileURL(join(tmp, "game.ts")).href);
  const find = (id) => data.creatures.find((c) => c.id === id);
  const lower = (s) => s.toLowerCase();
  const out = (name, cases) => {
    writeFileSync(join(here, `${name}.json`), JSON.stringify(cases, null, 1) + "\n");
    console.log(`${name}.json  ${cases.length} cases`);
  };

  // ---------------------------------------------------------------- damage
  const dmg = (name, attacker_id, attacker_level, defender_id, power = 1, guard = false) => {
    const a = find(attacker_id);
    const d = game.damage({ ...a, attack: a.attack + (attacker_level - 1) * 2 }, find(defender_id), power, guard);
    return { name, input: { attacker_id, attacker_level, defender_id, power, guard }, expected: { damage: d } };
  };
  out("damage", [
    dmg("Fire beats Earth (advantaged)", "cindertail", 1, "acornix"),
    dmg("Fire vs Water (neutral)", "cindertail", 1, "dewfin"),
    dmg("Water beats Fire", "dewfin", 1, "cindertail"),
    dmg("Earth beats Water", "mosslyn", 1, "dewfin"),
    dmg("Air beats Earth", "zephruff", 1, "mosslyn"),
    dmg("Earth vs Air (neutral)", "mosslyn", 1, "zephruff"),
    dmg("Light beats Dark", "lumoth", 1, "nightpurr"),
    dmg("Dark beats Light", "nightpurr", 1, "solcat"),
    dmg("Guard halves damage", "cindertail", 1, "acornix", 1, true),
    dmg("Skill power 1.65", "mosslyn", 5, "breezlet", 1.65),
    dmg("Level scaling (+2 atk/level)", "cindertail", 4, "petalume"),
    dmg("Floor of 4", "breezlet", 1, "acornix", 0.1),
    dmg("Wave-scaled enemy power", "acornix", 1, "mosslyn", 1 + (3 - 1) * 0.12),
  ]);

  // --------------------------------------------------------------- variant
  const fams = ["Feline", "Canine", "Avian", "Rodent", "Insect"];
  out(
    "variant",
    fams.flatMap((f) =>
      ["day", "rain", "night"].map((a) => ({
        name: `${f} / ${a}`,
        input: { family: lower(f), attunement: a },
        expected: { creature_id: game.chooseVariant(f, a).id },
      })),
    ),
  );

  // ----------------------------------------------------------- familiarity
  const DAY = 86400000;
  const enc = (e) => ({ ...e, family: lower(e.family) });
  const tag = (t) => ({ "New encounter": "newEncounter", "Probably familiar": "probablyFamiliar", "Returning presence": "returningPresence" })[t];
  const famOracle = (name, current, history) => ({
    name,
    input: { current: enc(current), history: history.map(enc) },
    expected: { tag: tag(game.familiarity(current, history)) },
  });
  const famHand = (name, current, history, expectedTag) => ({
    name,
    input: { current: enc(current), history: history.map(enc) },
    expected: { tag: expectedTag },
  });
  const now = { family: "Feline", time: 10 * DAY, lat: 23.81, lon: 90.41 };
  out("familiarity", [
    famOracle("same family, place and week", now, [{ ...now, time: now.time - 100000 }]),
    famOracle("too far away", now, [{ ...now, time: now.time - 100000, lat: 24 }]),
    famOracle("different family", now, [{ ...now, time: now.time - 100000, family: "Canine" }]),
    famOracle("two prior matches -> returning", now, [{ ...now, time: now.time - 2 * DAY }, { ...now, time: now.time - DAY }]),
    famOracle("exactly 7 days ago -> new", now, [{ ...now, time: now.time - 7 * DAY }]),
    famOracle("future-dated history ignored", now, [{ ...now, time: now.time + 1000 }]),
    famOracle("insect within 60 m (44 m)", { ...now, family: "Insect" }, [{ ...now, family: "Insect", lat: 23.8104, time: now.time - 1000 }]),
    famOracle("insect outside 60 m (78 m)", { ...now, family: "Insect" }, [{ ...now, family: "Insect", lat: 23.8107, time: now.time - 1000 }]),
    famOracle("canine within 300 m (278 m)", { ...now, family: "Canine" }, [{ ...now, family: "Canine", lat: 23.8125, time: now.time - 1000 }]),
    famOracle("demo matches demo", { family: "Avian", time: 5 * DAY, demo: true }, [{ family: "Avian", time: 4 * DAY, demo: true }]),
    famOracle("two demo matches -> returning", { family: "Avian", time: 5 * DAY, demo: true }, [{ family: "Avian", time: 4 * DAY, demo: true }, { family: "Avian", time: 3 * DAY, demo: true }]),
    famOracle("demo never matches real", { ...now, demo: true }, [{ ...now, time: now.time - 1000 }]),
    famHand("(R8) no location: family + recency fallback", { family: "Feline", time: 5 * DAY }, [{ family: "Feline", time: 4 * DAY }], "probablyFamiliar"),
    famHand("(R8) no location: capped below returning", { family: "Feline", time: 5 * DAY }, [{ family: "Feline", time: 4 * DAY }, { family: "Feline", time: 3 * DAY }], "probablyFamiliar"),
    famHand("(R8) current located, history not: fallback", now, [{ family: "Feline", time: now.time - DAY }], "probablyFamiliar"),
    famHand("(R8) one located + one unlocated match: capped", now, [{ ...now, time: now.time - DAY }, { family: "Feline", time: now.time - 2 * DAY }], "probablyFamiliar"),
    famHand("(R8) no location but older than 7 days -> new", { family: "Feline", time: 20 * DAY }, [{ family: "Feline", time: 10 * DAY }], "newEncounter"),
    famHand("(R8) no location, different family -> new", { family: "Feline", time: 5 * DAY }, [{ family: "Rodent", time: 4 * DAY }], "newEncounter"),
  ]);

  // ---------------------------------------------------------------- battle
  // Wave 1 only: the prototype always fields the wave-1 trio, which matches our
  // rotation at wave 1. Later waves differ by design (R18) and are unit-tested separately.
  const starters = [
    { id: "mosslyn", level: 5 },
    { id: "cindertail", level: 4 },
    { id: "dewfin", level: 3 },
  ];
  const run = (allies, wave, actions) => {
    let b = game.createBattle(allies.map((a) => a.id), wave, Object.fromEntries(allies.map((a) => [a.id, a.level])));
    let accepted = 0;
    for (const act of actions) {
      const n = game.battleTurn(b, act);
      if (n !== b) accepted++;
      b = n;
    }
    return {
      status: b.status,
      turn: b.turn,
      accepted_actions: accepted,
      allies_hp: b.allies.map((u) => u.hp),
      allies_max_hp: b.allies.map((u) => u.maxHp),
      enemies_hp: b.enemies.map((u) => u.hp),
      enemies_max_hp: b.enemies.map((u) => u.maxHp),
      cooldowns: b.allies.map((u) => u.cooldowns),
      active: b.active,
      target: b.target,
    };
  };
  const battleCase = (name, allies, wave, actions) => ({ name, input: { allies, wave, actions }, expected: run(allies, wave, actions) });
  // A greedy policy, recorded as a fixed action list so both engines replay the same thing.
  const greedy = (allies, wave, max = 400) => {
    let b = game.createBattle(allies.map((a) => a.id), wave, Object.fromEntries(allies.map((a) => [a.id, a.level])));
    const acts = [];
    while (b.status === "active" && acts.length < max) {
      const a = b.allies[b.active];
      const act = a.hp < a.maxHp * 0.35 && a.cooldowns[1] === 0 ? "heal" : a.cooldowns[0] === 0 ? "skill" : "basic";
      acts.push(act);
      b = game.battleTurn(b, act);
    }
    return acts;
  };
  const guardUntilDefeat = (() => {
    const allies = [{ id: "breezlet", level: 1 }, { id: "petalume", level: 1 }, { id: "acornix", level: 1 }];
    let b = game.createBattle(allies.map((a) => a.id), 1, {});
    const acts = [];
    while (b.status === "active" && acts.length < 400) { acts.push("guard"); b = game.battleTurn(b, "guard"); }
    return { allies, acts };
  })();
  out("battle", [
    battleCase("initial state, starter squad, wave 1", starters, 1, []),
    battleCase("skill on cooldown is rejected (no turn used)", starters, 1, ["skill", "skill"]),
    battleCase("skill cooldown expires after 2 actions", starters, 1, ["skill", "basic", "skill"]),
    battleCase("heal is capped at max HP", starters, 1, ["heal"]),
    battleCase("heal on cooldown is rejected", starters, 1, ["basic", "heal", "heal"]),
    battleCase("guard then basic", starters, 1, ["guard", "basic"]),
    battleCase("full victory (greedy policy)", starters, 1, greedy(starters, 1)),
    battleCase("full defeat (guard only, level-1 squad)", guardUntilDefeat.allies, 1, guardUntilDefeat.acts),
    battleCase("actions after victory are ignored", starters, 1, [...greedy(starters, 1), "basic", "skill"]),
  ]);

  // --------------------------------------------------------------- economy
  // Prototype economy lives inline in App.tsx (not importable); formulas ported from
  // there and from createBattle (max HP). See research R16.
  const maxHpOracle = (id, level) => game.createBattle([id], 1, { [id]: level }).allies[0].maxHp;
  out("economy", [
    { name: "train: +1 level, +5 bond", input: { op: "train", level: 4, bond: 24 }, expected: { level: 5, bond: 29 } },
    { name: "train: bond capped at 100", input: { op: "train", level: 9, bond: 98 }, expected: { level: 10, bond: 100 } },
    { name: "discover owned: +1 level, +15 bond", input: { op: "discover_owned", level: 3, bond: 18 }, expected: { level: 4, bond: 33 } },
    { name: "discover owned: bond capped", input: { op: "discover_owned", level: 3, bond: 90 }, expected: { level: 4, bond: 100 } },
    { name: "discover new: L1, bond 15", input: { op: "discover_new" }, expected: { level: 1, bond: 15 } },
    { name: "player level 249 xp", input: { op: "player_level", xp: 249 }, expected: { level: 1 } },
    { name: "player level 250 xp", input: { op: "player_level", xp: 250 }, expected: { level: 2 } },
    { name: "player level 0 xp", input: { op: "player_level", xp: 0 }, expected: { level: 1 } },
    { name: "max hp mosslyn L5", input: { op: "max_hp", creature_id: "mosslyn", level: 5 }, expected: { max_hp: maxHpOracle("mosslyn", 5) } },
    { name: "max hp lumoth L1", input: { op: "max_hp", creature_id: "lumoth", level: 1 }, expected: { max_hp: maxHpOracle("lumoth", 1) } },
    { name: "effective attack cindertail L4", input: { op: "effective_attack", creature_id: "cindertail", level: 4 }, expected: { attack: find("cindertail").attack + 3 * 2 } },
  ]);
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
