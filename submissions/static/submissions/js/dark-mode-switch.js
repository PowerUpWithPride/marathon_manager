// const BOOTSTRAP_DEFAULT = 'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css';
const BOOTSTRAP_DEFAULT = 'https://cdnjs.cloudflare.com/ajax/libs/bootswatch/4.3.1/flatly/bootstrap.min.css';
const BOOTSTRAP_DARK = 'https://cdnjs.cloudflare.com/ajax/libs/bootswatch/4.3.1/darkly/bootstrap.min.css';

$(function () {
    let darkSwitch = $("#darkSwitch");

    darkSwitch.prop('checked', localStorage.getItem("darkSwitch") !== null &&
        localStorage.getItem("darkSwitch") === "dark");

    darkSwitch.change(function (event) {
        if ($(event.target).prop('checked')) {
            localStorage.setItem("darkSwitch", "dark");
            $("#bootstrap-link").attr('href', BOOTSTRAP_DARK);
            document.dispatchEvent(new CustomEvent('darkMode', {detail: true}));
        } else {
            localStorage.removeItem("darkSwitch");
            $("#bootstrap-link").attr('href', BOOTSTRAP_DEFAULT);
            document.dispatchEvent(new CustomEvent('darkMode', {detail: true}));
        }
    }).change();
});
