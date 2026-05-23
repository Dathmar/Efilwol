document.addEventListener('alpine:init', () => {
    Alpine.data('gameController', () => ({
        battleLogs: [],
        gameStatus: null,
        selectedTarget: null,   // name of currently selected party member
        currentHeal: null,      // the heal button element currently casting
        currentHealToken: 0,    // bumped to abort in-flight animateCast loops
        isCasting: false,       // true while a heal is in progress
        aliveEnemies: 0,
        aliveParty: 0,
        gameLoopInterval: null,
        startTime: Date.now(),
        _cards: {},
        _expectedTotal: 0,
        _battleAborted: false,  // set true on victory/defeat to stop all in-flight attacks
        // The element that was selected when the cast started — never changes mid-cast
        _castTargetEl: null,

        init() {
            const expectedEnemies = document.querySelectorAll('[script_type="enemy"]').length;
            const expectedParty   = document.querySelectorAll('[script_type="player"], [script_type="lowlife"]').length;
            this._expectedTotal   = expectedEnemies + expectedParty;

            console.log(`Expecting ${expectedEnemies} enemies + ${expectedParty} party = ${this._expectedTotal} cards`);

            if (this._expectedTotal === 0) {
                this.addLog('ERROR: No characters found in page. Check game data.');
                return;
            }

            this.$el.addEventListener('script-card-ready', (e) => {
                const el   = e.detail.el;
                const id   = el.getAttribute('script_id');
                const name = el.getAttribute('script_name');
                const type = el.getAttribute('script_type');
                const key  = `${type}:${id}`;
                this._cards[key] = el;
                const ready = Object.keys(this._cards).length;
                console.log(`Card ready: [${type}] ${name} id=${id} (${ready}/${this._expectedTotal})`);
                if (ready === this._expectedTotal) this._startBattle();
            });
        },

        _startBattle() {
            console.log('All cards ready — starting battle!');
            this.updateCounters();
            this.addLog('Battle started! Choose your targets wisely.');

            this.$el.addEventListener('heal-cast', (e) => this.handleHealCast(e.detail));

            document.querySelectorAll('[script_type="player"], [script_type="lowlife"]').forEach(el => {
                el.addEventListener('click', () => this.selectTarget(el));
            });

            this.gameLoopInterval = setInterval(() => this.gameLoop(), 20);
        },

        _endBattle() {
            // Signal all in-flight attack animations to stop
            this._battleAborted = true;
            // Kill any in-flight heal cast immediately
            if (this.currentHeal) {
                this.currentHealToken++;
                Alpine.$data(this.currentHeal).stopCasting();
                this.currentHeal = null;
            }
            this.isCasting = false;
            this._castTargetEl = null;
        },

        _data(el) {
            return Alpine.$data(el);
        },

        // ----------------------------------------------------------------
        // Targeting — never interrupts a cast
        // ----------------------------------------------------------------
        selectTarget(el) {
            if (this.gameStatus !== null) return;
            // Just update the visual selection and selectedTarget name.
            // The in-flight cast (if any) will still heal _castTargetEl.
            document.querySelectorAll('.heal-selected').forEach(e => e.classList.remove('heal-selected'));
            el.classList.add('heal-selected');
            this.selectedTarget = el.getAttribute('script_name');
        },

        // ----------------------------------------------------------------
        // Abort — always available as a button while casting
        // ----------------------------------------------------------------
        abortCast() {
            if (!this.currentHeal) return;
            this.currentHealToken++;
            Alpine.$data(this.currentHeal).stopCasting();
            this.currentHeal = null;
            this.isCasting = false;
            this._castTargetEl = null;
            this.addLog('Cast aborted.');
        },

        // ----------------------------------------------------------------
        // Game loop
        // ----------------------------------------------------------------
        async gameLoop() {
            this.updateCounters();

            if (this.aliveEnemies === 0 && this.gameStatus === null) {
                this.gameStatus = 'victory';
                this.addLog('🎉 Victory! All enemies defeated!');
                clearInterval(this.gameLoopInterval);
                this._endBattle();
                return;
            }

            if (this.aliveParty === 0 && this.gameStatus === null) {
                this.gameStatus = 'defeat';
                this.addLog('💀 Defeat! Your party has fallen!');
                clearInterval(this.gameLoopInterval);
                this._endBattle();
                return;
            }

            document.querySelectorAll('[script_type="enemy"]').forEach(el => {
                const d = this._data(el);
                if (!d.isDead && !d.isAttacking) this.processAttack(el, 'party');
            });

            document.querySelectorAll('[script_type="player"]').forEach(el => {
                const d = this._data(el);
                if (!d.isDead && !d.isAttacking) this.processAttack(el, 'enemy');
            });
        },

        updateCounters() {
            this.aliveEnemies = Array.from(document.querySelectorAll('[script_type="enemy"]'))
                .filter(el => !this._data(el).isDead).length;
            this.aliveParty = Array.from(document.querySelectorAll('[script_type="player"], [script_type="lowlife"]'))
                .filter(el => !this._data(el).isDead).length;
        },

        // ----------------------------------------------------------------
        // Attack
        // ----------------------------------------------------------------
        async processAttack(sourceEl, targetType) {
            const selector = targetType === 'party'
                ? '[script_type="player"], [script_type="lowlife"]'
                : `[script_type="${targetType}"]`;

            const targets = Array.from(document.querySelectorAll(selector))
                .filter(el => !this._data(el).isDead);

            if (targets.length === 0) return;

            const targetEl = targets[Math.floor(Math.random() * targets.length)];
            const src      = this._data(sourceEl);
            const tgt      = this._data(targetEl);
            const sourceId = sourceEl.getAttribute('script_id');
            const targetId = targetEl.getAttribute('script_id');
            const srcType  = sourceEl.getAttribute('script_type');
            const srcName  = sourceEl.getAttribute('script_name');
            const tgtName  = targetEl.getAttribute('script_name');

            src.setAttacking(true);

            try {
                const res = await fetch(`/api/v1/game/attack/${sourceId}/${targetId}/1/${srcType}/`);
                if (!res.ok) throw new Error(`API ${res.status}`);
                const { cast_time, cool_down, damage_done, action_name, is_crit, type_multiplier, retry_after_ms } = await res.json();

                // No-action case: all actions on cooldown
                if (damage_done === 0 && action_name === null) {
                    this.addLog(`${srcName} has no available actions`);
                    return;
                }

                // Abort if battle ended or target already dead before animation starts
                if (this._battleAborted || tgt.isDead) return;

                const aborted = await this.animateAttack(sourceEl, targetEl, cast_time, cool_down);
                if (aborted) return;

                if (tgt.isDead) {
                    this.addLog(`${srcName} attacked ${tgtName} who died during the attack!`);
                    return;
                }

                tgt.takeDamage(damage_done);

                // Build enriched log message
                let msg = `${srcName} used ${action_name} on ${tgtName} for ${damage_done} damage`;
                if (is_crit) msg += ' — CRITICAL HIT!';
                if (type_multiplier > 1.0) msg += ' (effective)';
                if (type_multiplier < 1.0) msg += ' (glancing blow)';
                if (tgt.isDead) msg += ' — FATAL!';
                this.addLog(msg);
            } catch (err) {
                console.error('Attack error:', err);
            } finally {
                src.setAttacking(false);
            }
        },

        // Returns true if the animation was aborted (target died or battle ended)
        async animateAttack(sourceEl, targetEl, castTime, coolDown) {
            const steps = 50;
            const step  = (castTime + coolDown) / steps;
            const src   = this._data(sourceEl);
            const tgt   = this._data(targetEl);
            for (let i = 0; i <= steps; i++) {
                if (this._battleAborted || tgt.isDead) {
                    src.setAttackProgress(0);
                    return true;  // aborted
                }
                src.setAttackProgress((i / steps) * 100);
                await this.sleep(step);
            }
            src.setAttackProgress(0);
            return false;  // completed normally
        },

        // ----------------------------------------------------------------
        // Healing
        // ----------------------------------------------------------------
        async handleHealCast(detail) {
            if (this.gameStatus !== null) return;

            const btnEl = detail.button;

            // confirmCastCancel=true: heal buttons are disabled while casting
            if (this.isCasting && GAME_CONFIG.confirmCastCancel) return;

            // confirmCastCancel=false: abort current cast and start new one
            if (this.isCasting && !GAME_CONFIG.confirmCastCancel) {
                this.currentHealToken++;
                Alpine.$data(this.currentHeal).stopCasting();
                this.currentHeal = null;
                this.isCasting = false;
                this._castTargetEl = null;
                this.addLog('Cast interrupted.');
            }

            // Snapshot the target at cast-start — target changes mid-cast don't affect this
            const targetEl = document.querySelector('.heal-selected');
            if (!targetEl) {
                this.addLog('No target selected for healing!');
                return;
            }

            this.currentHealToken++;
            const myToken = this.currentHealToken;
            this.currentHeal = btnEl;
            this._castTargetEl = targetEl;
            this.isCasting = true;

            const btnData  = Alpine.$data(btnEl);
            const minHeal  = parseInt(btnEl.getAttribute('min_heal'));
            const maxHeal  = parseInt(btnEl.getAttribute('max_heal'));
            const castTime = parseInt(btnEl.getAttribute('cast_time'));
            const amount   = minHeal + Math.floor(Math.random() * (maxHeal - minHeal + 1));
            const casterEl = document.querySelector('[script_type="lowlife"]');

            btnData.startCasting();
            await this.animateCast(casterEl, castTime, myToken);

            // Bail if aborted
            if (myToken !== this.currentHealToken) return;

            // Apply heal to the target that was selected when the cast started
            const tgt = this._data(this._castTargetEl);
            const tgtName = this._castTargetEl.getAttribute('script_name');

            if (tgt.isDead) {
                this.addLog(`Heal failed — ${tgtName} is dead!`);
            } else {
                const actual = tgt.heal(amount);
                const over   = amount - actual;
                this.addLog(over > 0
                    ? `Healed ${tgtName} for ${actual} (${over} overheal)`
                    : `Healed ${tgtName} for ${actual}`
                );
            }

            btnData.stopCasting();
            this.currentHeal = null;
            this.isCasting = false;
            this._castTargetEl = null;
        },

        async animateCast(el, castTime, token) {
            if (!el) { await this.sleep(castTime); return; }
            const steps = 50;
            const step  = castTime / steps;
            const d     = this._data(el);
            for (let i = 0; i <= steps; i++) {
                if (token !== this.currentHealToken) {
                    d.setAttackProgress(0);
                    return;
                }
                // Abort mid-cast if the target died while we were casting
                if (this._castTargetEl && this._data(this._castTargetEl).isDead) {
                    d.setAttackProgress(0);
                    const tgtName = this._castTargetEl.getAttribute('script_name');
                    this.addLog(`Heal aborted — ${tgtName} died during cast!`);
                    // Bump token so the post-cast block in handleHealCast bails out
                    this.currentHealToken++;
                    Alpine.$data(this.currentHeal).stopCasting();
                    this.currentHeal = null;
                    this.isCasting = false;
                    this._castTargetEl = null;
                    return;
                }
                d.setAttackProgress((i / steps) * 100);
                await this.sleep(step);
            }
            d.setAttackProgress(0);
        },

        // ----------------------------------------------------------------
        // Utilities
        // ----------------------------------------------------------------
        addLog(message) {
            const ms = Date.now() - this.startTime;
            this.battleLogs.unshift({ time: `${(ms / 1000).toFixed(3)}s`, message });
            if (this.battleLogs.length > 50) this.battleLogs.pop();
        },

        sleep(ms) {
            return new Promise(r => setTimeout(r, ms));
        }
    }));
});
