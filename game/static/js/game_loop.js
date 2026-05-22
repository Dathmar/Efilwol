const enemies = document.querySelectorAll("[id^=id_enemy_]");
const scripts = document.querySelectorAll("[id^=id_player_]");
const lowlife = document.querySelector("[id^=id_lowlife_]");
const lowlife_heal_bar = document.getElementById('id_attack_value_lowlife_4');
const player_scripts = document.querySelectorAll("[id^=id_player_],[id^=id_lowlife_]");
const healz = document.getElementsByClassName('heal');

let selected_heal = null;
let currentHeal = null;

const start_time = Date.now();
const attack_log = document.getElementById("id_attack_log");
const icons = {
    sword: '<img src="/static/img/sword.svg" alt="Attack Notification">',
    tomb: '<img src="/static/img/tomb.svg" alt="Death Notification">',
    heal: '<img src="/static/img/heal.svg" alt="Heal Notification">'
};

function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function remove_heal_select(elm) {
    elm.classList.remove("heal-selected");
    elm.classList.add("border-0");
}

function add_heal_select(elm) {
    elm.classList.add("heal-selected");
    elm.classList.remove("border-0");
    selected_heal = elm;
}

function abort_heals() {
    if (currentHeal) {
        currentHeal.heal_btn.classList.remove('casting');
        currentHeal.heal_btn.disabled = false;

        // Reset the heal progress bar
        lowlife_heal_bar.style.transition = 'none';
        lowlife_heal_bar.style.width = '0%';

        currentHeal = null;
    }
}

function handleHealClick(event) {
    if (selected_heal !== null) {
        cast_heal(event.target, selected_heal);
    }
}

function handleScriptClick(event) {
    const clickedScript = event.target.closest("[id^=id_player_]");
    console.log(event.target);
    remove_heal_select(lowlife);
    scripts.forEach(script => {
        if (script !== clickedScript) {
            remove_heal_select(script);
        } else {
            add_heal_select(script);
        }
    });
}

function handleLowlifeClick() {
    add_heal_select(lowlife);
    scripts.forEach(remove_heal_select);
}

document.addEventListener("DOMContentLoaded", () => {
    lowlife.addEventListener("click", handleLowlifeClick);

    scripts.forEach(script =>
        script.addEventListener("click", handleScriptClick));

    Array.from(healz).forEach(heal_btn =>
        heal_btn.addEventListener("click", handleHealClick));

    main_loop();
});

async function apply_heal(amount, target) {
    const target_health_value = target.querySelector(`[id^=id_value_health_]`);
    const target_name = target.getAttribute('script_name');
    if (target_health_value.textContent === "0") {
        add_log_message(`You tried to heal ${target_name} but they were already dead`, icons.tomb);
        return;
    }

    const target_health = target.querySelector(`[id^=id_health_]`);
    let health_now = parseInt(target_health.getAttribute("aria-valuenow"));
    const max_health = parseInt(target_health.getAttribute("aria-valuemax"));
    let health_result = amount + health_now;
    let health_percent;
    let over_heal = 0;

    if (health_result > max_health) {
        over_heal = health_result - max_health;
        amount -= over_heal;
        health_result = max_health;
        health_percent = `100%`;
    } else {
        health_percent = `${parseInt((health_result / max_health) * 100)}%`;
    }

    target_health_value.style.width = health_percent;
    target_health_value.textContent = health_result;
    target_health.setAttribute("aria-valuenow", health_result);

    const message = over_heal !== 0
        ? `You healed ${target_name} for ${amount} and over healed for ${over_heal}`
        : `You healed ${target_name} for ${amount}`;

    add_log_message(message, icons.heal);
}

async function global_timeout(current_heal) {
    Array.from(healz).forEach(heal => {
        if (heal !== current_heal) {
            heal.disabled = true;
        }
    });

    await sleep(1000);

    Array.from(healz).forEach(heal => {
        if (heal !== current_heal) {
            heal.disabled = false;
        }
    });
}

async function cast_heal(heal_btn, target) {
    // Abort the current heal if a new heal is cast
    await abort_heals();
    // Set the current heal
    currentHeal = { heal_btn };

    global_timeout(heal_btn);
    heal_btn.classList.add('casting');
    heal_btn.disabled = true;

    const heal_amount = getRandomInt(parseInt(heal_btn.getAttribute('min_heal')), parseInt(heal_btn.getAttribute('max_heal')));
    const cast_time = parseInt(heal_btn.getAttribute('cast_time'));

    animate(lowlife_heal_bar, cast_time, 250);

    // Periodically check if the target is still alive during the attack animation
    // and that the cast hasn't been aborted
    const checkInterval = 100; // Check every 100ms
    let elapsedTime = 0;

    while (elapsedTime < cast_time) {
        await sleep(checkInterval);
        elapsedTime += checkInterval;

        if (target.classList.contains("dead") || lowlife.classList.contains("dead")) {
            add_log_message(`Heal aborted due to death`, icons.tomb);
            heal_btn.classList.remove("casting");
            heal_btn.disabled = false;
            // Stop the animation
            lowlife_heal_bar.style.transition = 'none';
            lowlife_heal_bar.style.width = '0%';
            return;
        }

        if (!heal_btn.classList.contains('casting')) {
            add_log_message(`Heal aborted`, icons.heal);
            heal_btn.classList.remove("casting");
            heal_btn.disabled = false;
            // Stop the animation
            lowlife_heal_bar.style.transition = 'none';
            lowlife_heal_bar.style.width = '0%';
            return;
        }
    }

    heal_btn.classList.remove('casting');
    heal_btn.disabled = false;

    if (!target.classList.contains('dead')) {
        apply_heal(heal_amount, target);
    }
}

async function main_loop() {
    let sum_health = 0;

    enemies.forEach(enemy => {
        const enemy_health = enemy.querySelector(`[id^=id_health_]`);
        sum_health += parseInt(enemy_health.getAttribute("aria-valuenow"));
        if (!enemy.classList.contains("attacking")) {
            const target_index = getRandomInt(0, player_scripts.length - 1);
            attack(enemy, player_scripts[target_index], target_index, 'player');
        }
    });

    if (sum_health === 0) {
        add_log_message(`You Won`);
        return;
    }

    sum_health = parseInt(lowlife.querySelector(`[id^=id_health_]`).getAttribute("aria-valuenow"));

    scripts.forEach(script => {
        const script_health = script.querySelector(`[id^=id_health_]`);
        sum_health += parseInt(script_health.getAttribute("aria-valuenow"));
        if (!script.classList.contains("attacking")) {
            const target_index = getRandomInt(0, enemies.length - 1);
            attack(script, enemies[target_index], target_index, 'enemy');
        }
    });

    if (sum_health === 0) {
        add_log_message(`You Lost`);
        return;
    }

    setTimeout(main_loop, 20);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function animate(element, duration, cool_down = 200) {
    transition.begin(element, [
        ["width", '0%', '100%']
    ], {
        duration: `${duration}ms`,
        timingFunction: "linear",
        onTransitionEnd: function (element, finished) {
            if (!finished) return;
            transition.begin(element, [
                ["width", '100%', '0%']
            ], {
                duration: `${cool_down}ms`,
                timingFunction: "linear",
            });
        }
    });
}

async function add_log_message(message, icon = null) {
    const time = Date.now() - start_time;
    const diffMs = time % 1000;
    const diffSec = Math.floor(time / 1000);

    const newParagraph = document.createElement("DIV");
    newParagraph.classList.add("row");

    const time_col = document.createElement("DIV");
    time_col.classList.add("col-2", "text-center", "my-auto");
    time_col.innerHTML = `${diffSec}.${diffMs}s`;

    const icon_col = document.createElement("DIV");
    icon_col.classList.add("col-1", "text-center", "my-auto");
    if (icon) {
        icon_col.innerHTML = icon;
    }

    const message_col = document.createElement("DIV");
    message_col.classList.add("col-9");
    message_col.innerHTML = message;

    newParagraph.appendChild(time_col);
    newParagraph.appendChild(icon_col);
    newParagraph.appendChild(message_col);

    attack_log.prepend(newParagraph);
}

async function choose_attack(source_id, target_id, attack_id, script_alignment) {
    const response = await fetch(`/api/v1/game/attack/${source_id}/${target_id}/${attack_id}/${script_alignment}/`);
    return response.json();
}

async function attack(source, target, target_index, type) {
    if (target.classList.contains("dead")) {
        return;
    }

    source.classList.add("attacking");
    const source_name = source.getAttribute('script_name');
    const source_id = source.getAttribute('script_id');
    const source_type = source.getAttribute('script_type');
    const target_name = target.getAttribute('script_name');
    const target_id = target.getAttribute('script_id');
    const attack_progress = source.querySelector(`[id^=id_attack_value_]`);

    const attack_details = await choose_attack(source_id, target_id, 1, source_type);
    const { cast_time, cool_down, damage_done: attack_strength } = attack_details;

    // Start the attack animation
    animate(attack_progress, cast_time, cool_down);

    // Periodically check if the target is still alive during the attack animation
    const checkInterval = 100; // Check every 100ms
    let elapsedTime = 0;

    while (elapsedTime < cast_time + cool_down) {
        await sleep(checkInterval);
        elapsedTime += checkInterval;

        if (target.classList.contains("dead")) {
            add_log_message(`${source_name} attacked ${target_name} who died during the attack!`, icons.tomb);
            source.classList.remove("attacking");
            // Stop the animation
            attack_progress.style.transition = 'none';
            attack_progress.style.width = '0%';
            return;
        }

        if (source.classList.contains("dead")) {
            add_log_message(`${source_name} attacked ${target_name} but died while trying!`, icons.tomb);
            // Stop the animation
            attack_progress.style.transition = 'none';
            attack_progress.style.width = '0%';
            return;
        }
    }

    const target_health_value = target.querySelector(`[id^=id_value_health_]`);

    if (target.classList.contains("dead")) {
        add_log_message(`${source_name} attacked ${target_name} who was already dead!`, icons.tomb);
        source.classList.remove("attacking");
        return;
    }

    add_log_message(`${source_name} attacked ${target_name} for ${attack_strength} damage!`, icons.sword);

    const target_health = target.querySelector(`[id^=id_health_]`);
    const max_health = parseInt(target_health.getAttribute("aria-valuemax"));
    let health_result = parseInt(target_health_value.textContent) - attack_strength;

    if (health_result <= 0) {
        health_result = 0;
        if (type === 'enemy') {
            enemies[target_index] = null;
        } else {
            player_scripts[target_index] = null;
        }
        add_log_message(`${target_name} died!`, icons.tomb);

        target_health_value.style.width = '0%';
        target_health_value.textContent = health_result;
        target_health.setAttribute("aria-valuenow", health_result);

        target.getElementsByClassName("dead")[0].classList.remove("d-none");
        target.getElementsByClassName("alive")[0].classList.add("d-none");
        target.classList.add("dead");
    } else {
        target_health_value.style.width = `${Math.round((health_result / max_health) * 100)}%`;
        target_health_value.textContent = health_result;
        target_health.setAttribute("aria-valuenow", health_result);
    }

    source.classList.remove("attacking");
}

