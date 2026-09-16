/**
 * FŐ INDÍTÓ
 *
 * Az összes riportcsoportot elindítja.
 */
function morningAutoRun() {
  Logger.log("Napi összesített indítás megkezdve...");

  processFmatracExports();          // 1. csoport: 7 db
  processPaymentPayoutExports();    // 2. csoport: 14 db
  processSzamlazzExports();         // 3. csoport: 3 csatolmány 1 emailben
  processReservationExports();      // 4. csoport: Amberlyn ResReport
  processOrderItemsExports();       // 5. csoport: Order items riportok
}


/**
 * ============================================================
 * 1. TÉMA: FMATRAC RIPORTOK
 * ============================================================
 */
function processFmatracExports() {
  var configs = [
    { subjectPrefix: "FMATRAC Riport - Maverick Athenaeum", folderId: "19bo5GiU6lrPEgfrSbJrO74e7pWD9Ng7U" },
    { subjectPrefix: "FMATRAC Riport - Maverick Downtown Apartment", folderId: "1HjE1CMPEIYHqG6HA7aPc5OqG0GAfHdXU" },
    { subjectPrefix: "FMATRAC Riport - Maverick Budapest Soho", folderId: "1fz1PwvGgmam-vZpg9SF3chn7s4ujTUYf" },
    { subjectPrefix: "FMATRAC Riport - Giselle Vintage Doubles", folderId: "1WWJ3dhu1yw2Lfw3ZxqTqaRtLsjLmg1ac" },
    { subjectPrefix: "FMATRAC Riport - Maverick Central Market", folderId: "1OlJCdki0z-TC1lrewUrL4f0nPzGAbpwO" },
    { subjectPrefix: "FMATRAC Riport - Giselle Buda Castle", folderId: "1xk3SOqhKWNPbRMkgZM1JleGwgYHN8p2K" },
    { subjectPrefix: "FMATRAC Riport - Amberlyn Management Kft.", folderId: "102qpagWkmb8j9NO7IU93D6qTVVYdBGKt" }
  ];

  runLogic(configs, "FMATRAC", "retryFmatrac");
}


/**
 * ============================================================
 * 2. TÉMA: PAYMENT ÉS PAYOUT RIPORTOK
 * ============================================================
 */
function processPaymentPayoutExports() {
  var configs = [
    { subjectPrefix: "Scheduled export of Payment report_GBC", folderId: "1SaF84GEvQlr8xN2R6KF1uOnhFayPVc_D" },
    { subjectPrefix: "Scheduled export of Payment report_ATH", folderId: "1KGd5i9yH9UxJw6yTSveZBpbwwaS3Hj6_" },
    { subjectPrefix: "Scheduled export of Payment report_SOHO", folderId: "1QD0ngN0Fa5vzmk7NrkszNsk3LjzV0DS3" },
    { subjectPrefix: "Scheduled export of Payment report_CENTRAL", folderId: "1TRgDr2i_JrE36GQAqQ6xsTG_k4q6V0QL" },
    { subjectPrefix: "Scheduled export of Payment report_DT", folderId: "1VVu8IXHmx9kFuo82Z-h7mvdvrrYfAiYQ" },
    { subjectPrefix: "Scheduled export of Payment report_GVD", folderId: "1IgjazIli9Kxn807Nyl4N_5xOfFObaXfI" },
    { subjectPrefix: "Scheduled export of Mews payout report_GBC", folderId: "1YW3v3__H92zsHrT1zQZreV9q9FsYYe23" },
    { subjectPrefix: "Scheduled export of payout_total_ATH", folderId: "11HFdIpgeEIPKR2hAguigkhCVa7aYOOYe" },
    { subjectPrefix: "Scheduled export of Mews payout report SOHO", folderId: "1avEyXVFme4VXLLsopnmyLIcAwFkH6g0L" },
    { subjectPrefix: "Scheduled export of Mews payout report_CENTRAL", folderId: "1u0lE84uJkrMNlswgHNXxtB7hFxhPlH2I" },
    { subjectPrefix: "Scheduled export of Mews payout report_DT", folderId: "1aFa3J4vAYAenmM2y9OwHrLfoM4eTM6E4" },
    { subjectPrefix: "Scheduled export of Mews payout report_GVD", folderId: "1hwWmPVt7aUiwHuOwTX0To8rF6fz2LzBb" },
    { subjectPrefix: "Scheduled export of Payment report Amberlyn", folderId: "1K0SeRyibeikLr9giUWgOQr5YlxncEvr4" },
    { subjectPrefix: "Scheduled export of Payout export Amberlyn", folderId: "1QSxQSYv6vKByO4zp8-MsswpSfkT5em7_" }
  ];

  runLogic(configs, "Payment/Payout", "retryPayment");
}


/**
 * ============================================================
 * 3. TÉMA: SZÁMLÁZZ.HU RIPORTOK (1 EMAILBEN A 3 CSATOLMÁNY)
 * ============================================================
 */
function processSzamlazzExports() {
  var processKey = "Szamlazz::CombinedVatReports";

  if (isProcessingDoneToday(processKey)) {
    Logger.log("Szamlazz - A mai ÁFA listák már fel lettek dolgozva.");
    cleanSpecificTriggers("retrySzamlazz");
    return;
  }

  var match = findLatestMessageBySubjectPrefixes(["Napi ÁFA Listák"]);

  if (!match) {
    Logger.log("Szamlazz - Még hiányzik a 'Napi ÁFA Listák' kezdetű levél.");
    setupSpecificTrigger("retrySzamlazz");
    return;
  }

  var companyMappings = [
    { codePrefix: "LBWSK", folderId: "1Se15CyfmRcECnOxCjOCLDK_EsEcikmBL", label: "Lebowski Kft." },
    { codePrefix: "MAUDE", folderId: "16KYmZhM-F08ZNHj-3VQf1TZXszHki1Cf", label: "Maude Hotel Kft." },
    { codePrefix: "MBRLY", folderId: "1jU3BiAy-iRgz3xvv0uFDu5WTeWqFFtj3", label: "Amberlyn Management Kft." }
  ];

  try {
    Logger.log("Szamlazz - Talált levél: " + match.subject);
    var attachments = getRealAttachments(match.message);

    if (attachments.length === 0) {
      throw new Error("A Számlázz.hu e-mailben nincs valódi csatolmány.");
    }

    var savedCount = 0;

    attachments.forEach(function(att) {
      var fileName = att.getName() || "";

      companyMappings.forEach(function(mapping) {
        if (fileName.indexOf(mapping.codePrefix) === 0) {
          var folder = DriveApp.getFolderById(mapping.folderId);
          var savedFile = folder.createFile(att.copyBlob());
          savedFile.setName(fileName);

          Logger.log("Szamlazz - [" + mapping.label + "] Csatolmány elmentve: " + fileName + " -> mappa: " + mapping.folderId);

          safeCleanOldFiles(folder, "Szamlazz::" + mapping.label);
          savedCount++;
        }
      });
    });

    if (savedCount === 0) {
      throw new Error("Egyetlen csatolmány sem felelt meg az ismert cégkódoknak (LBWSK, MAUDE, MBRLY).");
    }

    markProcessingDoneToday(processKey);
    cleanSpecificTriggers("retrySzamlazz");

    try {
      match.thread.moveToTrash();
    } catch (trashError) {
      Logger.log("Szamlazz - A levél kukázása nem sikerült: " + trashError.message);
    }

    Logger.log("Szamlazz - Sikeresen elmentve " + savedCount + " db ÁFA lista csatolmány.");

  } catch (e) {
    Logger.log("Szamlazz - Feldolgozási hiba: " + e.message);
    setupSpecificTrigger("retrySzamlazz");
    throw e;
  }
}


/**
 * ============================================================
 * 4. TÉMA: AMBERLYN RESERVATION REPORT
 * ============================================================
 */
function processReservationExports() {
  var config = {
    subjectPrefix: "Scheduled export of ResReport Amberlyn",
    attachmentFolderId: "1byLJxJlTywGIjisMscG3FpO76ZCjo53q",
    masterSpreadsheetId: "1j71wzNtQfssL3tIsKrzL_CX-ld16P0Cr5uRoFFRZTFg"
  };

  var processKey = "Reservation::" + config.attachmentFolderId;
  var attachmentStageKey = processKey + "::attachment_saved";

  if (isProcessingDoneToday(processKey)) {
    Logger.log("Reservation - A mai Amberlyn riport már teljesen feldolgozva.");
    cleanSpecificTriggers("retryReservation");
    return;
  }

  var match = findLatestMessageBySubjectPrefixes([config.subjectPrefix]);

  if (!match) {
    Logger.log("Reservation - Még hiányzik az ezzel kezdődő levél: " + config.subjectPrefix);
    setupSpecificTrigger("retryReservation");
    return;
  }

  var convertedSpreadsheetId = null;

  try {
    Logger.log("Reservation - Talált levél: " + match.subject);
    var attachments = getRealAttachments(match.message);

    if (attachments.length === 0) throw new Error("A Reservation emailben nincs valódi csatolmány.");
    var excelAttachment = findExcelAttachment(attachments);
    if (!excelAttachment) throw new Error("Nem található Excel-csatolmány a Reservation emailben.");

    Logger.log("Reservation csatolmány megtalálva: " + excelAttachment.getName());
    var attachmentFolder = DriveApp.getFolderById(config.attachmentFolderId);

    if (!isProcessingDoneToday(attachmentStageKey)) {
      var savedExcelFile = attachmentFolder.createFile(excelAttachment.copyBlob());
      savedExcelFile.setName(excelAttachment.getName());
      markProcessingDoneToday(attachmentStageKey);
      Logger.log("Reservation Excel elmentve: " + savedExcelFile.getName());
    }

    convertedSpreadsheetId = convertExcelBlobToGoogleSheet(
      excelAttachment.copyBlob(),
      "TEMP_AMBERLYN_RESREPORT_" + new Date().getTime()
    );

    appendReservationDataToMaster(convertedSpreadsheetId, config.masterSpreadsheetId);

    safeCleanOldFiles(attachmentFolder, "Reservation");
    markProcessingDoneToday(processKey);

    try {
      match.thread.moveToTrash();
    } catch (trashError) {}

    cleanSpecificTriggers("retryReservation");
    Logger.log("Amberlyn Reservation riport sikeresen feldolgozva.");

  } catch (e) {
    Logger.log("Amberlyn Reservation feldolgozási hiba: " + e.message);
    setupSpecificTrigger("retryReservation");
    throw e;
  } finally {
    if (convertedSpreadsheetId) {
      try { DriveApp.getFileById(convertedSpreadsheetId).setTrashed(true); } catch (e) {}
    }
  }
}

/**
 * ============================================================
 * 5. TÉMA: ORDER ITEMS RIPORTOK (ÚJ)
 * ============================================================
 */
function processOrderItemsExports() {
  var configs = [
    { name: "ATH", subjectPrefix: "Scheduled export of Order items report ATH", folderId: "18uH8eJ1B53ml41GNIYk4X8-0zU-5xBU2" },
    { name: "GBC", subjectPrefix: "Scheduled export of Order items report GBC", folderId: "152u0Z8ZifzdCOxZr9oTZH33uEhC0Tkst" },
    { name: "GVD", subjectPrefix: "Scheduled export of Order items report GVD", folderId: "1STmMW8m7sDDD-J8W72s0MsVNuQyKW1Cv" },
    { name: "SOHO", subjectPrefix: "Scheduled export of Order items report SOHO", folderId: "1WfW57pBQ08vOW4D1XNPCKAwCXSUlL-cd" }, 
    { name: "MVM", subjectPrefix: "Scheduled export of Order items report MVM", folderId: "1WHpj3hgNPG8qZzU8QiHUoN__Ip3WBGXL" },
    { name: "DWT", subjectPrefix: "Scheduled export of Order items report DWT", folderId: "1kEuu2pAitxAvpxkEzrs3ZrqivO_sK7p-" },
    { name: "AMB", subjectPrefix: "Scheduled export of Order items report AMB", folderId: "1wL9SLBdzOhU21CFUb5fS-pzehJNQGFHr" }
  ];

  var incompleteItems = [];

  configs.forEach(function(config) {
    var processKey = "OrderItems::" + config.name;
    
    // TESZTELÉS MIATT EZT A RÉSZT KIKOMMENTEZTÜK:
    // Így akárhányszor futtatod, mindig újra megpróbálja beolvasni az e-mailt!
    /*
    if (isProcessingDoneToday(processKey)) {
      Logger.log("OrderItems - Ma már feldolgozva: " + config.name);
      return;
    }
    */

    var match = findLatestMessageBySubjectPrefixes([config.subjectPrefix]);

    if (!match) {
      incompleteItems.push(config.name);
      Logger.log("OrderItems - Még hiányzik a levél: " + config.subjectPrefix);
      return;
    }

    var convertedSpreadsheetId = null;

    try {
      Logger.log("OrderItems - Talált levél: " + match.subject);
      var attachments = getRealAttachments(match.message);
      if (attachments.length === 0) throw new Error("Nincs valódi csatolmány.");

      var dataAttachment = findExcelAttachment(attachments) || attachments[0]; 
      
      var folder = DriveApp.getFolderById(config.folderId);
      
      // 1. Csatolmány fizikai mentése
      var savedFile = folder.createFile(dataAttachment.copyBlob());
      savedFile.setName(dataAttachment.getName());
      Logger.log("OrderItems - Napi fájl elmentve: " + savedFile.getName());

      // 2. Master fájl megkeresése vagy LÉTREHOZÁSA
      var masterFileName = "Master_OrderItems_" + config.name;
      var masterFileId = getOrCreateMasterSheet(folder, masterFileName);

      // 3. Napi adat konvertálása Google Sheet formátumba
      convertedSpreadsheetId = convertExcelBlobToGoogleSheet(
        dataAttachment.copyBlob(),
        "TEMP_ORDERITEMS_" + config.name + "_" + new Date().getTime()
      );

      // 4. "Items" munkalap kikeresése és adatok másolása a Master fájlba
      appendOrderItemsDataToMaster(convertedSpreadsheetId, masterFileId, config.name);

      // 5. Takarítás és lezárás
      safeCleanOldFiles(folder, "OrderItems::" + config.name); 
      
      // TESZTELÉS MIATT EZT IS KIKOMMENTEZTÜK (Nem regisztrálja készre a mai napra):
      // markProcessingDoneToday(processKey);

      try {
        match.thread.moveToTrash();
      } catch (trashError) {
        Logger.log("OrderItems - Levél kukázása nem sikerült: " + trashError.message);
      }
      
      Logger.log("OrderItems (" + config.name + ") sikeresen feldolgozva.");

    } catch (e) {
      Logger.log("OrderItems - Hiba (" + config.name + "): " + e.message);
      incompleteItems.push(config.name);
    } finally {
      if (convertedSpreadsheetId) {
        try { DriveApp.getFileById(convertedSpreadsheetId).setTrashed(true); } catch (e) {}
      }
    }
  });

  if (incompleteItems.length === 0) {
    Logger.log("OrderItems - Minden riport kész.");
    cleanSpecificTriggers("retryOrderItems");
  } else {
    Logger.log("OrderItems - Hiányzó/hibás elemek: " + incompleteItems.join(", ") + ". Újrapróbálkozás ütemezve.");
    setupSpecificTrigger("retryOrderItems");
  }
}

function getOrCreateMasterSheet(folder, masterFileName) {
  var files = folder.searchFiles("title = '" + masterFileName + "' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false");
  
  if (files.hasNext()) {
    return files.next().getId();
  } else {
    Logger.log("Master fájl nem létezik, új létrehozása: " + masterFileName);
    var newSpreadsheet = SpreadsheetApp.create(masterFileName);
    var file = DriveApp.getFileById(newSpreadsheet.getId());
    file.moveTo(folder);
    return file.getId();
  }
}

function appendOrderItemsDataToMaster(sourceSpreadsheetId, masterSpreadsheetId, propertyName) {
  var sourceSpreadsheet = openSpreadsheetWithRetry(sourceSpreadsheetId, 10, 1500);
  
  // Kizárólag az "Items" nevű fül kikeresése
  var sourceSheet = sourceSpreadsheet.getSheetByName("Items");
  
  if (!sourceSheet) {
    Logger.log("OrderItems (" + propertyName + ") - HIBA: Nem található 'Items' nevű munkalap a letöltött fájlban. A sorok nem lettek átmásolva.");
    return; // Ha nincs Items fül, kilép
  }

  var sourceValues = sourceSheet.getDataRange().getValues();

  if (sourceValues.length < 2) {
    Logger.log("OrderItems (" + propertyName + ") - Nincs feldolgozható adatsor az 'Items' fülön.");
    return;
  }

  var masterSpreadsheet = SpreadsheetApp.openById(masterSpreadsheetId);
  var masterSheet = masterSpreadsheet.getSheets()[0];
  var masterLastRow = masterSheet.getLastRow();

  // Fejléc másolása, ha a Master teljesen üres
  if (masterLastRow === 0) {
    masterSheet.getRange(1, 1, 1, sourceValues[0].length).setValues([sourceValues[0]]);
    masterLastRow = 1;
  }

  // Meglévő ID-k kigyűjtése az 'A' oszlopból a dublikáció szűréséhez
  var existingIds = {};
  if (masterLastRow >= 2) {
    var existingIdValues = masterSheet.getRange(2, 1, masterLastRow - 1, 1).getValues();
    existingIdValues.forEach(function(row) {
      if (row[0] !== "") existingIds[String(row[0]).trim()] = true;
    });
  }

  var rowsToAppend = [];
  // Adatok bejárása a 2. sortól (fejlécet átugorjuk)
  for (var rowIndex = 1; rowIndex < sourceValues.length; rowIndex++) {
    var row = sourceValues[rowIndex];
    if (!row || row.length === 0 || String(row[0]).trim() === "") continue; 

    var rowId = String(row[0]).trim(); 
    
    if (!existingIds[rowId]) {
      existingIds[rowId] = true;
      rowsToAppend.push(row);
    }
  }

  if (rowsToAppend.length === 0) {
    Logger.log("OrderItems (" + propertyName + ") - Nincs új, nem dublikált sor az 'Items' fülön.");
    return;
  }

  var requiredColumnCount = Math.max(masterSheet.getLastColumn(), getMaximumColumnCount(rowsToAppend));
  rowsToAppend = normalizeRowWidths(rowsToAppend, requiredColumnCount);

  var appendStartRow = masterSheet.getLastRow() + 1;
  masterSheet.getRange(appendStartRow, 1, rowsToAppend.length, requiredColumnCount).setValues(rowsToAppend);
  SpreadsheetApp.flush();

  Logger.log("OrderItems Master (" + propertyName + ") frissítve. Új sorok száma az 'Items' fülről: " + rowsToAppend.length);
}


/**
 * ============================================================
 * KÖZÖS CSATOLMÁNYMENTŐ MOTOR (1. ÉS 2. TÉMÁHOZ)
 * ============================================================
 */
function runLogic(configs, label, retryFunctionName) {
  var incompleteItems = [];
  var newlyProcessedCount = 0;
  var alreadyProcessedCount = 0;

  configs.forEach(function(config) {
    var prefixes = getSubjectPrefixes(config);
    var displayPrefix = prefixes.join(" VAGY ");
    var processKey = buildProcessingKey(label, config);

    if (isProcessingDoneToday(processKey)) {
      alreadyProcessedCount++;
      Logger.log(label + " - Ma már feldolgozva: " + displayPrefix);
      return;
    }

    var match = findLatestMessageBySubjectPrefixes(prefixes);

    if (!match) {
      incompleteItems.push(displayPrefix);
      Logger.log(label + " - Még hiányzik az ezzel kezdődő levél: " + displayPrefix);
      return;
    }

    try {
      Logger.log(label + " - Talált levél: " + match.subject);
      var attachments = getRealAttachments(match.message);

      if (attachments.length === 0) throw new Error("A levélben nincs valódi csatolmány.");

      var folder = DriveApp.getFolderById(config.folderId);

      attachments.forEach(function(att) {
        var savedFile = folder.createFile(att.copyBlob());
        if (att.getName()) savedFile.setName(att.getName());
        Logger.log(label + " - Csatolmány elmentve: " + att.getName());
      });

      safeCleanOldFiles(folder, label);
      markProcessingDoneToday(processKey);
      newlyProcessedCount++;

      try { match.thread.moveToTrash(); } catch (trashError) {}

    } catch (e) {
      incompleteItems.push(displayPrefix);
      Logger.log(label + " - Hiba (" + displayPrefix + "): " + e.message);
    }
  });

  var completedCount = newlyProcessedCount + alreadyProcessedCount;

  if (incompleteItems.length === 0) {
    Logger.log(label + " - Minden szükséges riport kész (" + completedCount + "/" + configs.length + ").");
    cleanSpecificTriggers(retryFunctionName);
  } else {
    Logger.log(label + " - Jelenleg kész: " + completedCount + "/" + configs.length + ". Újrapróbálkozás ütemezve.");
    setupSpecificTrigger(retryFunctionName);
  }
}


/**
 * ============================================================
 * TÁRGY-PREFIX KEZELÉS, EMAILEK ÉS TÖBBI SEGÉD
 * ============================================================
 */
function getSubjectPrefixes(config) {
  if (config.subjectPrefixes && config.subjectPrefixes.length > 0) return config.subjectPrefixes;
  if (config.subjectPrefix) return [config.subjectPrefix];
  if (config.subject) return [config.subject];
  throw new Error("A konfigurációból hiányzik a subjectPrefix.");
}

function subjectStartsWithAnyPrefix(actualSubject, prefixes) {
  var subject = String(actualSubject || "");
  for (var i = 0; i < prefixes.length; i++) {
    if (subject.indexOf(prefixes[i]) === 0) return true;
  }
  return false;
}

var RECENT_ATTACHMENT_MESSAGES_CACHE = null;

function findLatestMessageBySubjectPrefixes(prefixes) {
  var recentMessages = getRecentAttachmentMessages();
  var latestMatch = null;

  recentMessages.forEach(function(item) {
    if (!subjectStartsWithAnyPrefix(item.subject, prefixes)) return;
    if (!latestMatch || item.date.getTime() > latestMatch.date.getTime()) {
      latestMatch = item;
    }
  });

  return latestMatch;
}

function getRecentAttachmentMessages() {
  if (RECENT_ATTACHMENT_MESSAGES_CACHE !== null) return RECENT_ATTACHMENT_MESSAGES_CACHE;

  var result = [];
  var cutoffTime = new Date().getTime() - (24 * 60 * 60 * 1000);
  var query = "newer_than:1d has:attachment -in:trash";
  var pageSize = 100, maximumThreads = 500;

  for (var start = 0; start < maximumThreads; start += pageSize) {
    var batch = GmailApp.search(query, start, pageSize);
    if (batch.length === 0) break;

    batch.forEach(function(thread) {
      thread.getMessages().forEach(function(message) {
        var messageDate = message.getDate();
        if (messageDate.getTime() < cutoffTime) return;

        result.push({
          thread: thread, message: message, messageId: message.getId(),
          subject: message.getSubject() || "", date: messageDate
        });
      });
    });
    if (batch.length < pageSize) break;
  }
  RECENT_ATTACHMENT_MESSAGES_CACHE = result;
  return result;
}

function getRealAttachments(message) {
  return message.getAttachments({ includeInlineImages: false, includeAttachments: true });
}

/**
 * ============================================================
 * NAPI FELDOLGOZÁSI ÁLLAPOT
 * ============================================================
 */
var DAILY_STATE_PROPERTY_NAME = "REPORT_DAILY_PROCESSING_STATE_V2";

function getTodayDateKey() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd");
}

function getDailyProcessingState() {
  var raw = PropertiesService.getScriptProperties().getProperty(DAILY_STATE_PROPERTY_NAME);
  var today = getTodayDateKey();
  if (!raw) return { date: today, done: {} };
  try {
    var parsed = JSON.parse(raw);
    if (parsed.date !== today || !parsed.done) return { date: today, done: {} };
    return parsed;
  } catch (e) {
    return { date: today, done: {} };
  }
}

function saveDailyProcessingState(state) {
  PropertiesService.getScriptProperties().setProperty(DAILY_STATE_PROPERTY_NAME, JSON.stringify(state));
}

function isProcessingDoneToday(processKey) {
  return getDailyProcessingState().done[processKey] === true;
}

function markProcessingDoneToday(processKey) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var state = getDailyProcessingState();
    state.done[processKey] = true;
    saveDailyProcessingState(state);
  } finally {
    lock.releaseLock();
  }
}

function buildProcessingKey(label, config) {
  var uniquePart = config.key || config.folderId || config.attachmentFolderId || getSubjectPrefixes(config)[0];
  return label + "::" + uniquePart;
}

function resetDailyProcessingState() {
  PropertiesService.getScriptProperties().deleteProperty(DAILY_STATE_PROPERTY_NAME);
  RECENT_ATTACHMENT_MESSAGES_CACHE = null;
}

/**
 * ============================================================
 * EXCEL ÉS MASTER SHEET SEGÉDFÜGGVÉNYEK
 * ============================================================
 */
function findExcelAttachment(attachments) {
  for (var i = 0; i < attachments.length; i++) {
    var fileName = attachments[i].getName().toLowerCase();
    if (fileName.endsWith(".xlsx") || fileName.endsWith(".xls") || fileName.endsWith(".xlsm") || fileName.endsWith(".csv")) {
      return attachments[i];
    }
  }
  return null;
}

function convertExcelBlobToGoogleSheet(excelBlob, temporaryName) {
  var convertedFile = Drive.Files.create(
    { name: temporaryName, mimeType: "application/vnd.google-apps.spreadsheet" },
    excelBlob, { fields: "id" }
  );
  if (!convertedFile || !convertedFile.id) throw new Error("Az Excel konvertálása nem sikerült.");
  return convertedFile.id;
}

function openSpreadsheetWithRetry(spreadsheetId, maximumAttempts, waitMilliseconds) {
  for (var attempt = 1; attempt <= maximumAttempts; attempt++) {
    try { return SpreadsheetApp.openById(spreadsheetId); } 
    catch (e) { if (attempt < maximumAttempts) Utilities.sleep(waitMilliseconds); else throw e; }
  }
}

function appendReservationDataToMaster(sourceSpreadsheetId, masterSpreadsheetId) {
  var sourceSpreadsheet = openSpreadsheetWithRetry(sourceSpreadsheetId, 10, 1500);
  var sourceSheets = sourceSpreadsheet.getSheets();
  if (sourceSheets.length < 2) throw new Error("A Reservation Excelnek nincs 2. munkalapja.");

  var sourceValues = sourceSheets[1].getDataRange().getValues();
  if (sourceValues.length < 2) return;

  var masterSpreadsheet = SpreadsheetApp.openById(masterSpreadsheetId);
  var masterSheet = masterSpreadsheet.getSheets()[0];
  cleanMasterNonNumericRows(masterSheet);
  var masterLastRow = masterSheet.getLastRow();

  var existingIds = {};
  if (masterLastRow >= 2) {
    masterSheet.getRange(2, 1, masterLastRow - 1, 1).getValues().forEach(function(row) {
      var normalizedId = normalizeNumericId(row[0]);
      if (normalizedId !== null) existingIds[normalizedId] = true;
    });
  }

  var rowsToAppend = [];
  for (var i = 1; i < sourceValues.length; i++) {
    var row = sourceValues[i];
    if (!row || row.length === 0) continue;
    var normalizedId = normalizeNumericId(row[0]);
    if (normalizedId === null || existingIds[normalizedId]) continue;

    existingIds[normalizedId] = true;
    row[0] = Number(normalizedId);
    rowsToAppend.push(row);
  }

  if (rowsToAppend.length === 0) return;

  var requiredColumnCount = Math.max(masterSheet.getLastColumn(), getMaximumColumnCount(rowsToAppend));
  rowsToAppend = normalizeRowWidths(rowsToAppend, requiredColumnCount);

  masterSheet.getRange(masterSheet.getLastRow() + 1, 1, rowsToAppend.length, requiredColumnCount).setValues(rowsToAppend);
  SpreadsheetApp.flush();
}

function cleanMasterNonNumericRows(sheet) {
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  var values = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (var i = values.length - 1; i >= 0; i--) {
    if (normalizeNumericId(values[i][0]) === null) sheet.deleteRow(i + 2);
  }
}

function normalizeNumericId(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" && isFinite(value)) return String(Math.trunc(value));
  var text = String(value).trim();
  if (/^\d+(\.0+)?$/.test(text)) return text.replace(/\.0+$/, "");
  return null;
}

function getMaximumColumnCount(rows) {
  var maximum = 0;
  rows.forEach(function(row) { if (row.length > maximum) maximum = row.length; });
  return maximum;
}

function normalizeRowWidths(rows, columnCount) {
  return rows.map(function(row) {
    var nRow = row.slice(0, columnCount);
    while (nRow.length < columnCount) nRow.push("");
    return nRow;
  });
}

/**
 * ============================================================
 * 30 NAPOS DRIVE-TAKARÍTÁS (A Master fájlokat NEM törli, 
 * csak a 'Master' szó nélküli napi mentéseket)
 * ============================================================
 */
function cleanOldFiles(folder) {
  var expirationDate = new Date(new Date().getTime() - (30 * 24 * 60 * 60 * 1000));
  var files = folder.getFiles();

  while (files.hasNext()) {
    var file = files.next();
    // Védjük a Master fájlokat a törléstől!
    if (file.getDateCreated() < expirationDate && file.getName().indexOf("Master_") === -1) {
      file.setTrashed(true);
    }
  }
}

function safeCleanOldFiles(folder, label) {
  try { cleanOldFiles(folder); } 
  catch (e) { Logger.log(label + " - Takarítás hiba: " + e.message); }
}


/**
 * ============================================================
 * RETRY FÜGGVÉNYEK
 * ============================================================
 */
function retryFmatrac() { processFmatracExports(); }
function retryPayment() { processPaymentPayoutExports(); }
function retrySzamlazz() { processSzamlazzExports(); }
function retryReservation() { processReservationExports(); }
function retryOrderItems() { processOrderItemsExports(); } 

function setupSpecificTrigger(funcName) {
  cleanSpecificTriggers(funcName);
  ScriptApp.newTrigger(funcName).timeBased().after(2 * 60 * 60 * 1000).create();
}

function cleanSpecificTriggers(funcName) {
  ScriptApp.getProjectTriggers().forEach(function(trigger) {
    if (trigger.getHandlerFunction() === funcName) ScriptApp.deleteTrigger(trigger);
  });
}
